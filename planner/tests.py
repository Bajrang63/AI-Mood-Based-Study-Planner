from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Subject, Task, StudyPlan, StudyBlock, StudyHistory
from .services import build_plan

@override_settings(SECURE_SSL_REDIRECT=False,STATIC_ROOT=None)
class PlannerTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('bajrang',password='SampleUniquePassword93!')
        self.other=User.objects.create_user('other',password='SampleUniquePassword94!')
        self.subject=Subject.objects.create(user=self.user,name='Database systems')
        self.task=Task.objects.create(user=self.user,subject=self.subject,title='SQL joins',estimated_minutes=60,due_date=timezone.localdate(),priority=3)
        self.client.force_login(self.user)
    def data(self,**changes):
        data={'title':'Exam preparation','mood':'Tired','focus':4,'minutes':120,'intensity':'auto','start':timezone.now().replace(second=0,microsecond=0)}
        data.update(changes);return data
    def plan(self,**changes): return build_plan(self.user,self.data(**changes))
    def test_pages_and_saved_plan(self):
        plan=self.plan()
        for name in ['home','tasks','history']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertContains(self.client.get(reverse('plan_detail',args=[plan.pk])),'SQL joins')
        self.client.session.flush()
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('plan_detail',args=[plan.pk])).status_code,200)
    def test_schedule_duration_and_continuity(self):
        for minutes in [15,25,30,60,120,480]:
            for intensity in ['Light','Moderate','Intense']:
                plan=self.plan(minutes=minutes,intensity=intensity)
                cursor=plan.starts_at
                blocks=list(plan.blocks.all())
                self.assertEqual(sum(b.minutes for b in blocks),minutes)
                for b in blocks:
                    self.assertGreater(b.minutes,0);self.assertEqual(b.starts_at,cursor)
                    cursor+=timedelta(minutes=b.minutes)
    def test_deadline_order_and_allocation(self):
        task=Task.objects.create(user=self.user,subject=self.subject,title='Later',estimated_minutes=60,due_date=timezone.localdate()+timedelta(days=3))
        first=self.plan();self.assertEqual(first.blocks.first().task,self.task)
        self.assertEqual(sum(self.task.studyblock_set.values_list('minutes',flat=True)),60)
        second=self.plan()
        self.assertFalse(second.blocks.filter(task=self.task).exists())
        self.assertEqual(sum(task.studyblock_set.values_list('minutes',flat=True)),60)
    def test_create_and_reject_invalid_inputs(self):
        response=self.client.post(reverse('predict'),self.data())
        self.assertEqual(response.status_code,302)
        self.assertEqual(StudyPlan.objects.count(),1)
        for data in [self.data(minutes=-1),self.data(mood='Unknown'),self.data(focus=99),self.data(minutes=481)]:
            self.assertEqual(self.client.post(reverse('predict'),data).status_code,400)
        self.assertEqual(StudyPlan.objects.count(),1)
    def test_user_isolation(self):
        plan=self.plan();block=plan.blocks.first()
        self.client.force_login(self.other)
        for name,args in [('plan_detail',[plan.pk]),('download_plan',[plan.pk])]:
            self.assertEqual(self.client.get(reverse(name,args=args)).status_code,404)
        self.assertEqual(self.client.post(reverse('toggle_block',args=[block.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('toggle_task',args=[self.task.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('tasks'),{'action':'task','title':'Sneak','subject':self.subject.pk,'estimated_minutes':30,'difficulty':1,'priority':1}).status_code,200)
        self.assertEqual(Task.objects.count(),1)
    def test_completion_and_export(self):
        plan=self.plan();block=plan.blocks.first()
        self.assertEqual(self.client.get(reverse('toggle_block',args=[block.pk])).status_code,405)
        self.client.post(reverse('toggle_block',args=[block.pk]))
        block.refresh_from_db();self.assertTrue(block.completed)
        self.assertContains(self.client.get(reverse('home')),f'{block.minutes}')
        response=self.client.get(reverse('download_plan',args=[plan.pk]))
        self.assertContains(response,'SQL joins');self.assertContains(response,'True')
    def test_legacy_history_preserved(self):
        StudyHistory.objects.create(user=self.user,mood='Happy',hours=2,focus=6,intensity='Moderate')
        self.assertContains(self.client.get(reverse('history')),'Earlier study history')
    def test_password_validation_and_logout_method(self):
        self.client.logout()
        response=self.client.post(reverse('register'),{'username':'weak','password1':'123456','password2':'123456'})
        self.assertEqual(response.status_code,200);self.assertFalse(User.objects.filter(username='weak').exists())
        self.assertEqual(self.client.get(reverse('logout')).status_code,405)
    def test_auth_required_and_csrf(self):
        self.client.logout();self.assertEqual(self.client.get(reverse('home')).status_code,302)
        from django.test import Client
        client=Client(enforce_csrf_checks=True);client.force_login(self.user)
        self.assertEqual(client.post(reverse('predict'),self.data()).status_code,403)
    @patch('planner.ml_model.cached_model',return_value=None)
    def test_explanation_and_override(self,_):
        plan=self.plan();self.assertEqual(plan.intensity,'Light');self.assertIn('rules',plan.explanation)
        plan=self.plan(intensity='Moderate');self.assertEqual(plan.intensity,'Moderate');self.assertIn('You chose',plan.explanation)

    def test_reschedule_preserves_completed_work_and_releases_reserved_time(self):
        old=self.plan();block=old.blocks.first();block.completed=True;block.save()
        response=self.client.post(reverse('reschedule_plan',args=[old.pk]))
        self.assertEqual(response.status_code,302)
        old.refresh_from_db();self.assertTrue(old.archived)
        new=StudyPlan.objects.exclude(pk=old.pk).get()
        self.assertEqual(new.minutes,old.minutes-block.minutes)
        self.assertEqual(sum(new.blocks.filter(task=self.task).values_list('minutes',flat=True)),self.task.estimated_minutes-block.minutes)
        self.assertEqual(self.client.post(reverse('toggle_block',args=[block.pk])).status_code,404)
        self.assertEqual(self.client.post(reverse('reschedule_plan',args=[old.pk])).status_code,404)
    def test_edit_task_ownership(self):
        url=reverse('edit_task',args=[self.task.pk])
        self.assertEqual(self.client.get(url).status_code,200)
        data={'title':'Updated joins','subject':self.subject.pk,'estimated_minutes':45,'difficulty':2,'priority':3}
        self.assertEqual(self.client.post(url,data).status_code,302)
        self.task.refresh_from_db();self.assertEqual(self.task.title,'Updated joins')
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code,404)
    def test_login_throttle(self):
        from django.core.cache import cache
        cache.clear();self.client.logout()
        for _ in range(10):self.client.post(reverse('login'),{'username':'bajrang','password':'wrong'})
        self.assertEqual(self.client.post(reverse('login'),{'username':'bajrang','password':'wrong'}).status_code,429)
        cache.clear()
