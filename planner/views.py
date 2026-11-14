import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import RegisterForm, PlanForm, SubjectForm, TaskForm
from .models import StudyPlan, StudyBlock, Subject, Task, StudyHistory
from .services import build_plan

@login_required
def home_view(request):
    blocks=StudyBlock.objects.filter(plan__user=request.user,kind='study').exclude(plan__archived=True,completed=False)
    planned=blocks.aggregate(n=Sum('minutes'))['n'] or 0
    completed=blocks.filter(completed=True).aggregate(n=Sum('minutes'))['n'] or 0
    plans=StudyPlan.objects.filter(user=request.user)
    week=timezone.now()-timedelta(days=7)
    initial={'start':timezone.localtime().replace(second=0,microsecond=0),'mood':'Happy','intensity':'auto'}
    return render(request,'index.html',{'page':'home','form':PlanForm(initial=initial),'plans':plans[:3],'tasks':Task.objects.filter(user=request.user,completed=False).select_related('subject').order_by('due_date','-priority')[:5],'plan_count':plans.count(),'completed_minutes':completed,'completion':round(completed/planned*100) if planned else 0,'week_minutes':blocks.filter(completed=True,starts_at__gte=week).aggregate(n=Sum('minutes'))['n'] or 0,'open_tasks':Task.objects.filter(user=request.user,completed=False).count()})

@login_required
@require_POST
def predict_view(request):
    form=PlanForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            # Serialize planning for this account to avoid duplicate task allocation.
            User.objects.select_for_update().get(pk=request.user.pk)
            plan=build_plan(request.user,form.cleaned_data)
        return redirect('plan_detail',pk=plan.pk)
    return render(request,'plan_form.html',{'form':form,'page':'home'},status=400)

@login_required
def result_view(request):
    plan=StudyPlan.objects.filter(user=request.user).first()
    if not plan:
        messages.info(request,'Create your first plan to get started.')
        return redirect('home')
    return redirect('plan_detail',pk=plan.pk)

@login_required
def plan_detail(request,pk):
    plan=get_object_or_404(StudyPlan,user=request.user,pk=pk)
    blocks=list(plan.blocks.select_related('task'))
    study=sum(b.minutes for b in blocks if b.kind=='study')
    done=sum(b.minutes for b in blocks if b.kind=='study' and b.completed)
    return render(request,'result.html',{'plan':plan,'blocks':blocks,'study_minutes':study,'break_minutes':plan.minutes-study,'completion':round(done/study*100) if study else 0,'page':'result'})

@login_required
@require_POST
def toggle_block(request,pk):
    with transaction.atomic():
        block=get_object_or_404(StudyBlock.objects.select_for_update(),plan__user=request.user,plan__archived=False,pk=pk)
        block.completed=not block.completed
        block.save(update_fields=['completed'])
    return redirect('plan_detail',pk=block.plan_id)

@login_required
def tasks_view(request):
    subject_form=SubjectForm(); task_form=TaskForm(user=request.user)
    if request.method=='POST':
        if request.POST.get('action')=='subject':
            subject_form=SubjectForm(request.POST)
            if subject_form.is_valid():
                if Subject.objects.filter(user=request.user,name=subject_form.cleaned_data['name']).exists(): subject_form.add_error('name','This subject already exists.')
                else:
                    subject=subject_form.save(commit=False);subject.user=request.user;subject.save()
                    return redirect('tasks')
        else:
            task_form=TaskForm(request.POST,user=request.user)
            if task_form.is_valid():
                task=task_form.save(commit=False);task.user=request.user;task.save()
                return redirect('tasks')
    return render(request,'tasks.html',{'page':'tasks','subject_form':subject_form,'task_form':task_form,'subjects':Subject.objects.filter(user=request.user),'tasks':Task.objects.filter(user=request.user).select_related('subject').order_by('completed','due_date','-priority')})

@login_required
@require_POST
def toggle_task(request,pk):
    task=get_object_or_404(Task,user=request.user,pk=pk)
    task.completed=not task.completed;task.save(update_fields=['completed'])
    return redirect('tasks')

@login_required
def history_view(request):
    from django.core.paginator import Paginator
    plans=StudyPlan.objects.filter(user=request.user).prefetch_related('blocks')
    return render(request,'history.html',{'page':'history','plans':Paginator(plans,12).get_page(request.GET.get('page')),'legacy':StudyHistory.objects.filter(user=request.user)[:20]})

@login_required
def download_csv(request,pk=None):
    response=HttpResponse(content_type='text/csv');response['Content-Disposition']='attachment; filename="study-plan.csv"'
    writer=csv.writer(response)
    if pk is not None:
        plan=get_object_or_404(StudyPlan,user=request.user,pk=pk)
        writer.writerow(['Plan','Start','Type','Task','Minutes','Completed'])
        # Prefix free text so spreadsheet software cannot interpret it as a formula.
        safe=lambda x: "'"+x if x.lstrip().startswith(('=','+','-','@')) else x
        for b in plan.blocks.all():writer.writerow([safe(plan.title),timezone.localtime(b.starts_at).isoformat(),b.kind,safe(b.title),b.minutes,b.completed])
    else:
        writer.writerow(['Date','Title','Mood','Minutes','Focus','Intensity'])
        for p in StudyPlan.objects.filter(user=request.user):writer.writerow([p.starts_at.isoformat(),"'"+p.title,p.mood,p.minutes,p.focus,p.intensity])
    return response

def login_view(request):
    if request.user.is_authenticated:return redirect('home')
    form=AuthenticationForm(request,data=request.POST or None)
    import hashlib
    key='login-attempt:'+hashlib.sha256((request.META.get('REMOTE_ADDR','')+'|'+request.POST.get('username','').casefold()).encode()).hexdigest()
    attempts=cache.get(key,0)
    if request.method=='POST':
        if attempts>=10:
            form.add_error(None,'Too many sign-in attempts. Please try again in 10 minutes.')
            return render(request,'login.html',{'form':form,'page':'login'},status=429)
        if form.is_valid():
            cache.delete(key);login(request,form.get_user());return redirect('home')
        cache.set(key,attempts+1,600)
    return render(request,'login.html',{'form':form,'page':'login'})

def register_view(request):
    if request.user.is_authenticated:return redirect('home')
    form=RegisterForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        try:
            with transaction.atomic():user=form.save()
        except IntegrityError:form.add_error('username','This username is already taken.')
        else:login(request,user);return redirect('home')
    return render(request,'login.html',{'form':form,'page':'register'})

@require_POST
def logout_view(request):
    logout(request);return redirect('login')

@login_required
def chart_data_api(request):
    plans=StudyPlan.objects.filter(user=request.user).order_by('-created_at')[:30]
    return JsonResponse({'plans':[{'date':p.starts_at.isoformat(),'mood':p.mood,'focus':p.focus,'minutes':p.minutes} for p in plans]})


@login_required
def edit_task(request,pk):
    task=get_object_or_404(Task,user=request.user,pk=pk)
    form=TaskForm(request.POST or None,instance=task,user=request.user)
    if request.method=='POST' and form.is_valid():
        form.save()
        messages.success(request,'Task updated. Existing plans keep their original schedule; new plans use your updated task.')
        return redirect('tasks')
    return render(request,'edit_task.html',{'form':form,'page':'tasks'})


@login_required
@require_POST
def reschedule_plan(request,pk):
    with transaction.atomic():
        User.objects.select_for_update().get(pk=request.user.pk)
        old=get_object_or_404(StudyPlan.objects.select_for_update(),user=request.user,pk=pk,archived=False)
        done=sum(old.blocks.filter(completed=True).values_list('minutes',flat=True))
        remaining=old.minutes-done
        if remaining<15:
            messages.info(request,'Less than 15 minutes remain. Create a new plan for a fresh session.')
            return redirect('plan_detail',pk=old.pk)
        old.archived=True;old.save(update_fields=['archived'])
        new=build_plan(request.user,{'title':old.title+' · continued' if len(old.title)<108 else old.title,'mood':old.mood,'focus':old.focus,'minutes':remaining,'start':timezone.now().replace(second=0,microsecond=0),'intensity':old.intensity})
    messages.success(request,'Unfinished time replanned from now. Your previous plan and completed blocks are preserved.')
    return redirect('plan_detail',pk=new.pk)
