from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        REQUESTER = 'requester', 'Requester'
        ADMINISTRATOR = 'administrator', 'Administrator'
        WORKER = 'worker', 'Maintenance worker'
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REQUESTER)

class Ticket(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        ASSIGNED = 'assigned', 'Assigned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
    class Category(models.TextChoices):
        ELECTRICAL = 'Electrical'
        PLUMBING = 'Plumbing'
        FURNITURE = 'Furniture'
        HVAC = 'HVAC'
        OTHER = 'Other'
    class Priority(models.TextChoices):
        LOW = 'Low'
        MEDIUM = 'Medium'
        HIGH = 'High'
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_tickets')
    worker = models.ForeignKey(User, null=True, blank=True, on_delete=models.PROTECT, related_name='assigned_tickets')
    location = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField(max_length=1000)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    resolution_note = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ['-updated_at', '-id']
        constraints = [models.CheckConstraint(condition=models.Q(version__gte=1), name='positive_ticket_version')]

class History(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name='history')
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at', 'id']

class LoginAttempt(models.Model):
    username = models.CharField(max_length=150, db_index=True)
    ip = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
