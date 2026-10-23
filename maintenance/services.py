"""All permission and transition rules live here, not in templates."""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from .models import Ticket, History, User

class Conflict(Exception):
    pass

def visible_tickets(user):
    qs = Ticket.objects.select_related('owner', 'worker')
    if user.role == User.Role.ADMINISTRATOR:
        return qs
    if user.role == User.Role.REQUESTER:
        return qs.filter(owner=user)
    if user.role == User.Role.WORKER:
        return qs.filter(worker=user)
    return qs.none()

def can_read(user, ticket):
    return (user.role == User.Role.ADMINISTRATOR or
            user.role == User.Role.REQUESTER and ticket.owner_id == user.id or
            user.role == User.Role.WORKER and ticket.worker_id == user.id)

def can_act(user, ticket, action):
    if action in ('assign', 'priority'):
        return user.role == User.Role.ADMINISTRATOR
    if action in ('start', 'resolve'):
        return user.role == User.Role.WORKER and ticket.worker_id == user.id
    return False

@transaction.atomic
def create_ticket(user, data):
    if user.role != User.Role.REQUESTER:
        raise PermissionDenied
    ticket = Ticket.objects.create(owner=user, **data)
    History.objects.create(ticket=ticket, actor=user, action='Submitted', changes={
        'status': {'old': None, 'new': ticket.status}, 'priority': {'old': None, 'new': ticket.priority}})
    return ticket

@transaction.atomic
def update_ticket(user, ticket_id, action, data):
    # SQLite IMMEDIATE transactions serialize writes; conditional version update also guards stale forms.
    ticket = Ticket.objects.select_related('worker').get(pk=ticket_id)
    if not can_act(user, ticket, action):
        raise PermissionDenied
    if data['version'] != ticket.version:
        raise Conflict('This request changed. Reload the page before trying again.')
    if ticket.status == Ticket.Status.RESOLVED:
        raise Conflict('This action is not allowed in the current status.')
    updates = {}
    if action == 'assign':
        worker = data['worker']
        if not User.objects.filter(pk=worker.pk, role=User.Role.WORKER, is_active=True).exists():
            raise Conflict('That worker is no longer available. Reload and choose another worker.')
        updates['worker_id'] = worker.id
        if ticket.status == Ticket.Status.SUBMITTED:
            updates['status'] = Ticket.Status.ASSIGNED
    elif action == 'priority':
        updates['priority'] = data['priority']
    elif action == 'start' and ticket.status == Ticket.Status.ASSIGNED:
        updates['status'] = Ticket.Status.IN_PROGRESS
    elif action == 'resolve' and ticket.status == Ticket.Status.IN_PROGRESS:
        updates.update(status=Ticket.Status.RESOLVED, resolution_note=data['resolution_note'], resolved_at=timezone.now())
    else:
        raise Conflict('This action is not allowed in the current status.')
    changes = {k: {'old': getattr(ticket, k), 'new': v} for k,v in updates.items()
               if k in ('status', 'priority', 'worker_id') and getattr(ticket, k) != v}
    if not changes:
        return ticket
    updates.update(version=ticket.version + 1, updated_at=timezone.now())
    if Ticket.objects.filter(pk=ticket.pk, version=data['version']).update(**updates) != 1:
        raise Conflict('This request changed. Reload the page before trying again.')
    History.objects.create(ticket=ticket, actor=user, action={'assign':'Worker assigned','priority':'Priority changed',
                           'start':'Work started','resolve':'Resolved'}[action], changes=changes)
    ticket.refresh_from_db()
    return ticket
