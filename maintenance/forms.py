from django import forms
from .models import Ticket, User

class ReportForm(forms.Form):
    location = forms.CharField(min_length=3, max_length=100, label='Building and room',
                               widget=forms.TextInput(attrs={'placeholder': 'e.g. Library Room 204'}))
    category = forms.ChoiceField(choices=Ticket.Category.choices)
    description = forms.CharField(min_length=10, max_length=1000, widget=forms.Textarea(attrs={'rows': 5}),
                                  help_text='Describe the problem and where to find it. Use fictional data for this demo.')

class ActionForm(forms.Form):
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)

class AssignForm(ActionForm):
    worker = forms.ModelChoiceField(queryset=User.objects.filter(role=User.Role.WORKER, is_active=True), empty_label='Choose a worker')

class PriorityForm(ActionForm):
    priority = forms.ChoiceField(choices=Ticket.Priority.choices)

class ResolveForm(ActionForm):
    resolution_note = forms.CharField(min_length=10, max_length=1000, label='Resolution note',
                                      widget=forms.Textarea(attrs={'rows': 3}), help_text='Explain the repair in at least 10 characters.')
