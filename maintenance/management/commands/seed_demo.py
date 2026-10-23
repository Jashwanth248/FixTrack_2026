import os
import secrets
from django.core.management.base import BaseCommand, CommandError
from maintenance.models import User, Ticket
from maintenance.services import create_ticket, update_ticket

class Command(BaseCommand):
    help = 'Create fictional demo accounts and requests once. Never resets existing accounts or records.'
    def handle(self, *args, **options):
        if User.objects.exists():
            raise CommandError('Accounts already exist. Seed skipped to protect existing work. See README for a fresh demo.')
        password = os.environ.get('FIXTRACK_DEMO_PASSWORD') or secrets.token_urlsafe(12)
        if len(password) < 12:
            raise CommandError('Use a demo password of at least 12 characters.')
        users={}
        for name,role,first in [('student','requester','Alex'),('student2','requester','Sam'),
                                ('admin','administrator','Casey'),('worker','worker','Jordan'),('worker2','worker','Taylor')]:
            users[name]=User.objects.create_user(username=name,password=password,role=role,first_name=first)
        examples=[('Library Room 204','Electrical','Projector will not turn on during class.'),
                  ('Science Hall Room 110','Plumbing','The sink faucet continues dripping after being closed.'),
                  ('Student Center Room 12','Furniture','A chair leg is loose near the study tables.'),
                  ('Arts Building Room 305','HVAC','The air conditioning is not cooling the room.'),
                  ('Library Reading Area','Other','The window blind is stuck in the lowered position.')]
        for index,(location,category,description) in enumerate(examples):
            owner = users['student2'] if index == 4 else users['student']
            t=create_ticket(owner,dict(location=location,category=category,description=description))
            if index in (1,2,3):
                t=update_ticket(users['admin'],t.pk,'assign',{'worker':users['worker'],'version':t.version})
            if index in (2,3):
                t=update_ticket(users['worker'],t.pk,'start',{'version':t.version})
            if index == 3:
                update_ticket(users['worker'],t.pk,'resolve',{'version':t.version,'resolution_note':'Replaced the thermostat batteries and verified cooling.'})
        self.stdout.write(self.style.SUCCESS('Created five fictional accounts and five requests.'))
        self.stdout.write('Usernames: student, student2, admin, worker, worker2')
        self.stdout.write('Local demo password for these accounts: '+password)
        self.stdout.write('Keep this password locally. Do not publish it or use real campus data.')
