import ipaddress
from datetime import timedelta
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from .models import Ticket, User, LoginAttempt
from .forms import ReportForm, ActionForm, AssignForm, PriorityForm, ResolveForm
from .services import visible_tickets, can_read, can_act, create_ticket, update_ticket, Conflict

@require_http_methods(['GET', 'POST'])
def sign_in(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    status = 200
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()[:150]
        password = request.POST.get('password', '')
        try:
            ip = str(ipaddress.ip_address(request.META.get('REMOTE_ADDR', '127.0.0.1')))
        except ValueError:
            ip = '127.0.0.1'
        recent = LoginAttempt.objects.filter(created_at__gt=timezone.now()-timedelta(minutes=10))
        if recent.filter(username=username).count() >= 5 or recent.filter(ip=ip).count() >= 5:
            error, status = 'Too many sign-in attempts. Please wait up to 10 minutes and try again.', 429
        else:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                request.session['last_activity'] = timezone.now().timestamp()
                return redirect('dashboard')
            LoginAttempt.objects.create(username=username, ip=ip)
            error = 'Invalid username or password'
    return render(request, 'login.html', {'error':error}, status=status)

@require_POST
@login_required
def sign_out(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    qs = visible_tickets(request.user)
    counts = [(label, qs.filter(status=value).count()) for value,label in Ticket.Status.choices]
    selected = {k:request.GET.get(k, '') for k in ('status','category','priority')}
    for field, value in selected.items():
        if value:
            qs = qs.filter(**{field:value})
    page = Paginator(qs,20).get_page(request.GET.get('page'))
    return render(request, 'dashboard.html', {'page':page,'counts':counts,'selected':selected,
        'statuses':Ticket.Status.choices,'categories':Ticket.Category.choices,'priorities':Ticket.Priority.choices,
        'query':urlencode(selected)})

@login_required
@require_http_methods(['GET', 'POST'])
def report(request):
    if request.user.role != User.Role.REQUESTER:
        raise PermissionDenied
    form = ReportForm(request.POST or None)
    error = None
    if request.method == 'POST':
        if set(request.POST)-set(form.fields)-{'csrfmiddlewaretoken'}:
            return HttpResponseBadRequest('Unexpected fields. Reload the form.')
        if form.is_valid():
            try:
                ticket = create_ticket(request.user, form.cleaned_data)
            except DatabaseError:
                error = 'Unable to save. Please try again.'
            else:
                messages.success(request, 'Your request has been submitted.')
                return redirect('detail', pk=ticket.pk)
    return render(request, 'report.html', {'form':form, 'error':error}, status=503 if error else 200)

def detail_context(ticket, action=None, bound=None):
    data={'version':ticket.version}
    forms={'assign_form':AssignForm(initial={**data,'worker':ticket.worker_id}),
           'priority_form':PriorityForm(initial={**data,'priority':ticket.priority}),
           'start_form':ActionForm(initial=data), 'resolve_form':ResolveForm(initial=data)}
    if bound is not None:
        forms[action+'_form']=bound
    return {'ticket':ticket, 'events':ticket.history.select_related('actor'), **forms}

@login_required
def detail(request, pk):
    ticket = get_object_or_404(Ticket.objects.select_related('owner','worker'), pk=pk)
    if not can_read(request.user, ticket):
        raise PermissionDenied
    return render(request, 'detail.html', detail_context(ticket))

@login_required
@require_POST
def action(request, pk, action):
    ticket = get_object_or_404(Ticket, pk=pk)
    if not can_act(request.user, ticket, action):
        raise PermissionDenied
    cls = {'assign':AssignForm, 'priority':PriorityForm, 'start':ActionForm, 'resolve':ResolveForm}[action]
    form = cls(request.POST)
    if set(request.POST)-set(form.fields)-{'csrfmiddlewaretoken'}:
        return HttpResponseBadRequest('Unexpected fields. Reload the form.')
    if not form.is_valid():
        context = detail_context(ticket, action, form)
        context['error'] = 'Please correct the fields below.'
        return render(request, 'detail.html', context, status=400)
    try:
        update_ticket(request.user, pk, action, form.cleaned_data)
    except Conflict as exc:
        return render(request, 'error.html', {'message':str(exc), 'back':pk}, status=409)
    except DatabaseError:
        return render(request, 'error.html', {'message':'Unable to save. Please try again.', 'back':pk}, status=503)
    messages.success(request, 'Request updated successfully.')
    return redirect('detail', pk=pk)

def review(request):
    return render(request, 'review.html')

def forbidden(request, exception):
    return render(request, 'error.html', {'message':'You do not have access to this request or action.'}, status=403)

def missing(request, exception):
    return render(request, 'error.html', {'message':'That page or request could not be found.'}, status=404)
