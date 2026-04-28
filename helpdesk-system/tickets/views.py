import json
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model
from django.db.models import Avg, DurationField, ExpressionWrapper, F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import LoginForm, RegisterForm, TicketForm, TicketUpdateForm
from .models import Ticket

User = get_user_model()

AUTH_EVENTS_FILE = Path(__file__).resolve().parents[1] / 'auth_events.json'
AUTH_USERS_FILE = Path(__file__).resolve().parents[1] / 'users.json'


def _load_json_file(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding='utf-8').strip()
        return json.loads(raw) if raw else []
    except json.JSONDecodeError:
        return []


def _save_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')


def _find_json_user(username):
    for user_data in _load_json_file(AUTH_USERS_FILE):
        if user_data.get('username') == username:
            return user_data
    return None


def _save_json_user(user_data):
    users = _load_json_file(AUTH_USERS_FILE)
    existing = _find_json_user(user_data.get('username'))
    if existing:
        users = [u if u.get('username') != user_data.get('username') else user_data for u in users]
    else:
        users.append(user_data)
    _save_json_file(AUTH_USERS_FILE, users)


def _sync_user_account(user_data, raw_password=None):
    username = user_data.get('username')
    defaults = {
        'email': user_data.get('email', ''),
        'first_name': user_data.get('first_name', ''),
        'last_name': user_data.get('last_name', ''),
    }
    user, created = User.objects.get_or_create(username=username, defaults=defaults)
    if not created:
        changed = False
        for field, value in defaults.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed = True
        if changed:
            user.save()
    if raw_password:
        if not user.check_password(raw_password):
            user.set_password(raw_password)
            user.save()
    return user


def _append_auth_event(event):
    AUTH_EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = []
    if AUTH_EVENTS_FILE.exists():
        try:
            raw = AUTH_EVENTS_FILE.read_text(encoding='utf-8').strip()
            if raw:
                data = json.loads(raw)
        except json.JSONDecodeError:
            data = []

    data.append(event)
    AUTH_EVENTS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')


def _get_client_ip(request):
    return request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user_data = _find_json_user(username)

        if user_data and check_password(password, user_data.get('password', '')):
            user = _sync_user_account(user_data, raw_password=password)
            login(request, user)
            _append_auth_event({
                'timestamp': timezone.now().isoformat(),
                'event': 'login',
                'username': username,
                'user_id': user.pk,
                'status': 'success',
                'remote_addr': _get_client_ip(request),
            })
            return redirect('dashboard')

        form.add_error(None, 'Invalid username or password.')
        _append_auth_event({
            'timestamp': timezone.now().isoformat(),
            'event': 'login',
            'username': username,
            'status': 'failed',
            'remote_addr': _get_client_ip(request),
        })

    return render(request, 'tickets/login.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        raw_password = form.cleaned_data.get('password1')
        user = form.save(commit=False)
        user.email = form.cleaned_data.get('email')
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.save()

        _save_json_user({
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'department': getattr(user, 'department', ''),
            'role': getattr(user, 'role', User.ROLE_ENDUSER),
            'password': make_password(raw_password),
        })

        _append_auth_event({
            'timestamp': timezone.now().isoformat(),
            'event': 'register',
            'username': user.username,
            'email': user.email,
            'status': 'success',
            'remote_addr': _get_client_ip(request),
        })

        login(request, user)
        messages.success(request, 'Registration successful. You are now logged in.')
        return redirect('dashboard')

    return render(request, 'tickets/register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    totals = {
        'total': Ticket.objects.count(),
        'open': Ticket.objects.filter(status=Ticket.STATUS_OPEN).count(),
        'in_progress': Ticket.objects.filter(status=Ticket.STATUS_IN_PROGRESS).count(),
        'pending': Ticket.objects.filter(status=Ticket.STATUS_PENDING).count(),
        'resolved': Ticket.objects.filter(status=Ticket.STATUS_RESOLVED).count(),
        'closed': Ticket.objects.filter(status=Ticket.STATUS_CLOSED).count(),
    }

    resolved_tickets = Ticket.objects.filter(resolved_date__isnull=False)
    average_resolution = None
    if resolved_tickets.exists():
        resolved_avg = resolved_tickets.aggregate(
            avg=Avg(ExpressionWrapper(F('resolved_date') - F('created_date'), output_field=DurationField()))
        )['avg']
        average_resolution = int(resolved_avg.total_seconds() / 60) if resolved_avg else None

    technicians = User.objects.filter(role=User.ROLE_TECHNICIAN)
    performance = []
    for tech in technicians:
        performance.append({
            'name': tech.get_full_name() or tech.username,
            'assigned': Ticket.objects.filter(assigned_to=tech).count(),
            'resolved': Ticket.objects.filter(assigned_to=tech, status=Ticket.STATUS_RESOLVED).count(),
        })

    if request.user.is_administrator():
        recent_tickets = Ticket.objects.all()[:8]
    elif request.user.is_technician():
        recent_tickets = Ticket.objects.filter(assigned_to=request.user)[:8]
    else:
        recent_tickets = Ticket.objects.filter(user=request.user)[:8]

    return render(request, 'tickets/dashboard.html', {
        'totals': totals,
        'average_resolution': average_resolution,
        'performance': performance,
        'recent_tickets': recent_tickets,
    })


@login_required
def ticket_list(request):
    if request.user.is_administrator():
        tickets = Ticket.objects.all()
    elif request.user.is_technician():
        tickets = Ticket.objects.filter(assigned_to=request.user)
    else:
        tickets = Ticket.objects.filter(user=request.user)

    query = request.GET.get('q', '')
    if query:
        tickets = tickets.filter(description__icontains=query)

    return render(request, 'tickets/ticket_list.html', {
        'tickets': tickets,
        'query': query,
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    if not (request.user.is_administrator() or request.user == ticket.user or request.user == ticket.assigned_to):
        messages.error(request, 'You do not have permission to view this ticket.')
        return redirect('ticket_list')

    form = TicketUpdateForm(request.POST or None, instance=ticket)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        if ticket.status == Ticket.STATUS_RESOLVED and not ticket.resolved_date:
            ticket.resolved_date = timezone.now()
        ticket.save()
        messages.success(request, 'Ticket updated successfully.')
        return redirect('ticket_detail', ticket_id=ticket.ticket_id)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'form': form,
    })


@login_required
def ticket_create(request):
    form = TicketForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.user_name = request.user.get_full_name() or request.user.username
        ticket.department = ticket.department or request.user.department
        ticket.save()
        messages.success(request, 'Your ticket has been submitted.')
        return redirect('ticket_detail', ticket_id=ticket.ticket_id)

    return render(request, 'tickets/ticket_form.html', {
        'form': form,
    })
