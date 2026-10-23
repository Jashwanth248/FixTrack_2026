from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.db import DatabaseError
from django.utils import timezone
from .models import User, Ticket, History, LoginAttempt
from .services import create_ticket, update_ticket, Conflict

class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student=User.objects.create_user(username='student',password='test-only-password',role='requester')
        cls.other=User.objects.create_user(username='other',password='test-only-password',role='requester')
        cls.admin=User.objects.create_user(username='admin',password='test-only-password',role='administrator')
        cls.worker=User.objects.create_user(username='worker',password='test-only-password',role='worker')
        cls.worker2=User.objects.create_user(username='worker2',password='test-only-password',role='worker')
    def setUp(self):
        self.data={'location':'Library Room 204','category':'Electrical','description':'The projector will not turn on.'}
        self.ticket=create_ticket(self.student,self.data)
    def signin(self,user):
        self.client.force_login(user)
    def post_action(self,user,action,**data):
        self.signin(user)
        self.ticket.refresh_from_db()
        return self.client.post(reverse('action',args=[self.ticket.pk,action]),{'version':self.ticket.version,**data})
    def assign(self):
        self.assertEqual(self.post_action(self.admin,'assign',worker=self.worker.pk).status_code,302)
    def test_complete_workflow(self):
        self.assign()
        self.assertEqual(self.post_action(self.worker,'start').status_code,302)
        self.assertEqual(self.post_action(self.worker,'resolve',resolution_note='Replaced cable and verified the projector works.').status_code,302)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status,'resolved')
        self.assertEqual(self.ticket.history.count(),4)
        self.assertIsNotNone(self.ticket.resolved_at)
        self.assertEqual(self.ticket.version,4)
    def test_login_invalid_and_inactive(self):
        self.assertContains(self.client.post('/login/',{'username':'student','password':'wrong'}),'Invalid username or password')
        self.student.is_active=False; self.student.save()
        self.assertContains(self.client.post('/login/',{'username':'student','password':'test-only-password'}),'Invalid username or password')
    def test_login_and_logout(self):
        self.assertEqual(self.client.post('/login/',{'username':'student','password':'test-only-password'}).status_code,302)
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/logout/').status_code,405)
        self.assertEqual(self.client.post('/logout/').status_code,302)
        self.assertEqual(self.client.get('/').status_code,302)
    def test_anonymous_protected(self):
        for url in ['/', '/requests/new/', f'/requests/{self.ticket.pk}/']:
            self.assertEqual(self.client.get(url).status_code,302)
        self.assertEqual(self.client.post(f'/requests/{self.ticket.pk}/start/',{'version':1}).status_code,302)
    def test_owner_scope_and_admin_scope(self):
        second=create_ticket(self.other,dict(self.data,location='Other private location'))
        self.signin(self.student)
        self.assertNotContains(self.client.get('/'),'Other private location')
        self.assertEqual(self.client.get(f'/requests/{second.pk}/').status_code,403)
        self.signin(self.admin)
        self.assertContains(self.client.get('/'),'Other private location')
    def test_assignment_restricts_workers(self):
        self.assign()
        self.signin(self.worker2)
        self.assertEqual(self.client.get(f'/requests/{self.ticket.pk}/').status_code,403)
        self.assertEqual(self.post_action(self.worker2,'start').status_code,403)
        self.assertEqual(self.post_action(self.admin,'assign',worker=self.worker2.pk).status_code,302)
        self.signin(self.worker)
        self.assertEqual(self.client.get(f'/requests/{self.ticket.pk}/').status_code,403)
        self.assertEqual(self.post_action(self.worker,'start').status_code,403)
    def test_wrong_role_and_unknown_action(self):
        self.assertEqual(self.post_action(self.student,'assign',worker=self.worker.pk).status_code,403)
        self.assertEqual(self.post_action(self.worker,'priority',priority='High').status_code,403)
        self.assertEqual(self.post_action(self.admin,'delete').status_code,403)
        for user in [self.admin,self.worker]:
            self.signin(user)
            self.assertEqual(self.client.post('/requests/new/',self.data).status_code,403)
    def test_missing_record(self):
        self.signin(self.admin)
        self.assertEqual(self.client.get('/requests/99999/').status_code,404)
    def test_invalid_transition_and_short_resolution(self):
        self.assign()
        self.assertEqual(self.post_action(self.worker,'resolve',resolution_note='Valid length but incorrect state.').status_code,409)
        self.post_action(self.worker,'start')
        self.assertEqual(self.post_action(self.worker,'start').status_code,409)
        self.assertEqual(self.post_action(self.worker,'resolve',resolution_note='short').status_code,400)
    def test_resolved_read_only(self):
        self.assign(); self.post_action(self.worker,'start')
        self.post_action(self.worker,'resolve',resolution_note='Completed repair and checked operation.')
        for user,action,data in [(self.worker,'resolve',{'resolution_note':'Attempted repeat resolution.'}),
                                 (self.admin,'priority',{'priority':'High'}),(self.admin,'assign',{'worker':self.worker2.pk})]:
            self.assertEqual(self.post_action(user,action,**data).status_code,409)
        self.assertEqual(self.ticket.history.count(),4)
    def test_stale_forms_no_lost_update(self):
        self.assign(); self.ticket.refresh_from_db(); old=self.ticket.version
        self.post_action(self.admin,'priority',priority='High')
        self.assertEqual(self.client.post(reverse('action',args=[self.ticket.pk,'priority']),{'version':old,'priority':'Low'}).status_code,409)
        self.ticket.refresh_from_db(); self.assertEqual(self.ticket.priority,'High')
    def test_priority_noop(self):
        self.post_action(self.admin,'priority',priority='Medium')
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.version,1)
        self.assertEqual(self.ticket.history.count(),1)
    def test_invalid_worker(self):
        self.assertEqual(self.post_action(self.admin,'assign',worker=self.student.pk).status_code,400)
        self.worker.is_active=False; self.worker.save()
        self.assertEqual(self.post_action(self.admin,'assign',worker=self.worker.pk).status_code,400)
    def test_field_validation_and_trim(self):
        self.signin(self.student)
        for field,value in [('location','ab'),('location','a'*101),('description','a'*9),('description','a'*1001),('category','Unsupported')]:
            response=self.client.post('/requests/new/',dict(self.data,**{field:value}))
            self.assertContains(response,'Please correct the highlighted fields')
        self.assertEqual(Ticket.objects.count(),1)
        for location,description in [('abc','d'*10),('a'*100,'d'*1000)]:
            self.assertEqual(self.client.post('/requests/new/',dict(self.data,location=location,description=description)).status_code,302)
        self.client.post('/requests/new/',dict(self.data,location='  Valid room  '))
        self.assertTrue(Ticket.objects.filter(location='Valid room').exists())
    def test_server_fields_rejected(self):
        self.signin(self.student)
        self.assertEqual(self.client.post('/requests/new/',dict(self.data,owner=self.other.pk)).status_code,400)
        self.assertEqual(self.post_action(self.admin,'priority',priority='High',status='resolved').status_code,400)
    def test_filters_pagination_and_empty(self):
        self.signin(self.student)
        for index in range(21): create_ticket(self.student,dict(self.data,location=f'Room {index}'))
        response=self.client.get('/?category=Electrical&status=submitted&priority=Medium')
        self.assertEqual(len(response.context['page']),20)
        self.assertTrue(response.context['page'].has_next())
        self.assertEqual(len(self.client.get('/?page=2').context['page']),2)
        self.assertContains(self.client.get('/?status=resolved'),'No matching requests')
    def test_html_escaped(self):
        self.ticket.description='<script>alert("xss")</script>'; self.ticket.save()
        self.signin(self.student)
        response=self.client.get(f'/requests/{self.ticket.pk}/')
        self.assertContains(response,'&lt;script&gt;')
        self.assertNotContains(response,'<script>')
    def test_csrf(self):
        client=Client(enforce_csrf_checks=True); client.force_login(self.student)
        self.assertEqual(client.post('/requests/new/',self.data).status_code,403)
        self.assertEqual(client.post('/logout/').status_code,403)
    def test_login_throttle_by_username_and_ip(self):
        for i in range(5): self.client.post('/login/',{'username':'student','password':'wrong'},REMOTE_ADDR=f'192.0.2.{i+1}')
        self.assertEqual(self.client.post('/login/',{'username':'student','password':'test-only-password'},REMOTE_ADDR='192.0.2.20').status_code,429)
        LoginAttempt.objects.all().delete()
        for i in range(5): self.client.post('/login/',{'username':f'unknown{i}','password':'wrong'})
        self.assertEqual(self.client.post('/login/',{'username':'student','password':'test-only-password'}).status_code,429)
        LoginAttempt.objects.update(created_at=timezone.now()-timedelta(minutes=11))
        self.assertEqual(self.client.post('/login/',{'username':'student','password':'test-only-password'}).status_code,302)
    def test_idle_timeout(self):
        self.signin(self.student); session=self.client.session
        session['last_activity']=(timezone.now()-timedelta(minutes=31)).timestamp(); session.save()
        self.assertEqual(self.client.get('/').status_code,302)
    def test_history_failure_rolls_back_create(self):
        with patch('maintenance.services.History.objects.create',side_effect=DatabaseError('injected')):
            with self.assertRaises(DatabaseError): create_ticket(self.student,self.data)
        self.assertEqual(Ticket.objects.count(),1)
    def test_history_failure_rolls_back_update(self):
        with patch('maintenance.services.History.objects.create',side_effect=DatabaseError('injected')):
            response=self.post_action(self.admin,'priority',priority='High')
        self.assertEqual(response.status_code,503)
        self.ticket.refresh_from_db(); self.assertEqual(self.ticket.priority,'Medium'); self.assertEqual(self.ticket.version,1)
    def test_review_and_forms_render(self):
        self.assertContains(self.client.get('/review/'),'Preliminary Design Review')
        self.signin(self.student)
        self.assertContains(self.client.get('/requests/new/'),'Report a campus issue')
        self.assertContains(self.client.get(f'/requests/{self.ticket.pk}/'),'Request history')
