from datetime import timedelta
from django.utils import timezone
from .models import StudyPlan, StudyBlock
from .ml_model import recommend_intensity


def build_plan(user, data):
    suggested, explanation = recommend_intensity(data['mood'],data['minutes'],data['focus'])
    intensity = suggested if data['intensity']=='auto' else data['intensity']
    if data['intensity']!='auto': explanation = f'You chose {intensity.lower()} intensity. '+explanation
    plan = StudyPlan.objects.create(user=user,title=data['title'],mood=data['mood'],focus=data['focus'],minutes=data['minutes'],intensity=intensity,explanation=explanation,starts_at=data['start'])
    # Subtract work already assigned to unfinished blocks so new plans do not duplicate it.
    tasks = list(user.task_set.filter(completed=False).select_related('subject'))
    tasks.sort(key=lambda t:(t.due_date or timezone.localdate()+timedelta(days=3650),-t.priority,t.difficulty if intensity=='Light' else -t.difficulty,t.pk))
    remaining = {}
    for task in tasks:
        assigned = sum(task.studyblock_set.filter(completed=False,plan__archived=False).values_list('minutes',flat=True))
        done = sum(task.studyblock_set.filter(completed=True).values_list('minutes',flat=True))
        remaining[task.pk] = max(0,task.estimated_minutes-assigned-done)
    study_size, break_size = {'Light':(25,10),'Moderate':(45,10),'Intense':(60,5)}[intensity]
    cursor=0; blocks=[]
    while cursor<data['minutes']:
        task=next((t for t in tasks if remaining[t.pk]>0),None)
        length=min(study_size,data['minutes']-cursor,remaining[task.pk] if task else study_size)
        blocks.append(StudyBlock(plan=plan,task=task,title=f'{task.subject.name} · {task.title}' if task else 'Independent revision & practice',kind='study',position=len(blocks),minutes=length,starts_at=data['start']+timedelta(minutes=cursor)))
        if task: remaining[task.pk]-=length
        cursor+=length
        if cursor<data['minutes']:
            length=min(break_size,data['minutes']-cursor)
            blocks.append(StudyBlock(plan=plan,title='Step away. Recharge.',kind='break',position=len(blocks),minutes=length,starts_at=data['start']+timedelta(minutes=cursor)))
            cursor+=length
    StudyBlock.objects.bulk_create(blocks)
    return plan
