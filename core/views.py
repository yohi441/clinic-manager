from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from datetime import date, datetime
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import LensType, Patient, PrescriptionRecord
from .forms import PatientForm
from django.http import HttpResponse, FileResponse, HttpResponseBadRequest
from django.db.utils import OperationalError
from django.conf import settings
import json, os, sqlite3, tempfile, shutil


def is_last_active_admin(user):
    if user.profile.role != 'admin' or not user.is_active:
        return False
    return User.objects.filter(
        is_superuser=False, profile__role='admin', is_active=True
    ).count() <= 1


def get_staff_context():
    users = User.objects.select_related('profile').filter(is_superuser=False).order_by('username')
    admin_active = User.objects.filter(is_superuser=False, profile__role='admin', is_active=True)
    last_admin_ids = set()
    if admin_active.count() <= 1:
        last_admin_ids = set(admin_active.values_list('pk', flat=True))
    return {'users': users, 'last_admin_ids': last_admin_ids}


def role_required(*roles):
    def check(user):
        return hasattr(user, 'profile') and user.profile.role in roles
    return user_passes_test(check)


@login_required
def staff_list(request):
    return render(request, 'settings/staff_list.html', get_staff_context())


@login_required
@require_POST
def staff_create(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    role = request.POST.get('role', 'staff')
    errors = []
    if not username:
        errors.append('Username is required.')
    if not password:
        errors.append('Password is required.')
    elif len(password) < 6:
        errors.append('Password must be at least 6 characters.')
    if username and User.objects.filter(username__iexact=username).exists():
        errors.append(f'Username "{username}" already taken.')
    if not errors:
        user = User.objects.create_user(username=username, password=password,
                                        first_name=first_name, last_name=last_name)
        user.profile.role = role
        user.profile.save()
    if request.headers.get('HX-Request'):
        response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
        if errors:
            response['HX-Trigger'] = json.dumps({'show-message': {'text': ' '.join(errors), 'type': 'error'}})
        else:
            response['HX-Trigger'] = json.dumps({
                'show-message': {'text': 'Staff member added.', 'type': 'success'},
                'clear-staff-form': '',
            })
        return response
    return redirect('staff-list')


@login_required
def staff_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', u.profile.role)
        error = None
        if not username:
            error = 'Username is required.'
        elif User.objects.filter(username__iexact=username).exclude(pk=pk).exists():
            error = f'Username "{username}" already taken.'
        elif is_last_active_admin(u) and role != 'admin':
            error = 'Cannot change the last active admin role.'
        if error:
            if request.headers.get('HX-Request'):
                response = render(request, 'settings/staff_edit.html', {
                    'u': u, 'error': error,
                    'submitted_first_name': first_name,
                    'submitted_last_name': last_name,
                    'submitted_username': username,
                })
                response['HX-Retarget'] = '#modal-container'
                return response
            return render(request, 'settings/staff_edit.html', {
                'u': u, 'error': error,
                'submitted_first_name': first_name,
                'submitted_last_name': last_name,
                'submitted_username': username,
            })
        u.first_name = first_name
        u.last_name = last_name
        u.username = username
        if password:
            u.set_password(password)
        u.profile.role = role
        u.save()
        u.profile.save()
        if request.headers.get('HX-Request'):
            response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Staff member updated.', 'type': 'success'}})
            return response
        return redirect('staff-list')
    if request.headers.get('HX-Request'):
        return render(request, 'settings/staff_edit.html', {'u': u})
    return render(request, 'settings/staff_edit.html', {'u': u})


@login_required
@require_POST
def staff_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if is_last_active_admin(user):
        if request.headers.get('HX-Request'):
            response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Cannot deactivate the last active admin.', 'type': 'error'}})
            return response
        return redirect('staff-list')
    user.is_active = not user.is_active
    user.save()
    if user.pk == request.user.pk and not user.is_active:
        if request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = reverse('login')
            return response
        return redirect('login')
    if request.headers.get('HX-Request'):
        response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
        status = 'activated' if user.is_active else 'deactivated'
        response['HX-Trigger'] = json.dumps({'show-message': {'text': f'{user.username} {status}.', 'type': 'success'}})
        return response
    return redirect('staff-list')


@login_required
@require_POST
def staff_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if is_last_active_admin(user):
        if request.headers.get('HX-Request'):
            response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Cannot delete the last active admin.', 'type': 'error'}})
            return response
        return redirect('staff-list')
    if request.headers.get('HX-Request'):
        if user == request.user:
            response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Cannot delete yourself.', 'type': 'error'}})
            return response
        username = user.username
        user.delete()
        response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
        response['HX-Trigger'] = json.dumps({'show-message': {'text': f'{username} deleted.', 'type': 'success'}})
        return response
    if user == request.user:
        return redirect('staff-list')
    user.delete()
    return redirect('staff-list')


@login_required
@require_POST
def staff_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    password = request.POST.get('password', '')
    if request.headers.get('HX-Request'):
        response = render(request, 'settings/staff_list.html#staff_table', get_staff_context())
        if not password:
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Password is required.', 'type': 'error'}})
        else:
            user.set_password(password)
            user.save()
            response['HX-Trigger'] = json.dumps({'show-message': {'text': f'Password reset for {user.username}.', 'type': 'success'}})
        return response
    if password:
        user.set_password(password)
        user.save()
    return redirect('staff-list')


@login_required
def lens_type_list(request):
    types = LensType.objects.all().order_by('name')
    return render(request, 'settings/lens_type_list.html', {'types': types})


@login_required
@require_POST
def lens_type_create(request):
    name = request.POST.get('name', '').strip()
    errors = []
    if not name:
        errors.append('Name is required.')
    elif LensType.objects.filter(name__iexact=name).exists():
        errors.append(f'Lens type "{name}" already exists.')
    else:
        LensType.objects.create(name=name)
    types = LensType.objects.all().order_by('name')
    if request.headers.get('HX-Request'):
        response = render(request, 'settings/lens_type_list.html#lens_type_table', {'types': types})
        if errors:
            response['HX-Trigger'] = json.dumps({'show-message': {'text': ' '.join(errors), 'type': 'error'}})
        else:
            response['HX-Trigger'] = json.dumps({
                'show-message': {'text': 'Lens type added.', 'type': 'success'},
                'clear-lens-type-form': '',
            })
        return response
    return redirect('lens-type-list')


@login_required
def lens_type_edit(request, pk):
    lt = get_object_or_404(LensType, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        error = None
        if not name:
            error = 'Name is required.'
        elif LensType.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            error = f'Lens type "{name}" already exists.'
        else:
            lt.name = name
            lt.save()
        if request.headers.get('HX-Request'):
            if error:
                response = render(request, 'settings/lens_type_edit.html', {'lt': lt, 'error': error, 'submitted_name': name})
                response['HX-Retarget'] = '#modal-container'
                return response
            types = LensType.objects.all().order_by('name')
            response = render(request, 'settings/lens_type_list.html#lens_type_table', {'types': types})
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Lens type updated.', 'type': 'success'}})
            return response
        return redirect('lens-type-list')
    if request.headers.get('HX-Request'):
        return render(request, 'settings/lens_type_edit.html', {'lt': lt})
    return render(request, 'settings/lens_type_edit.html', {'lt': lt})


@login_required
@require_POST
def lens_type_toggle(request, pk):
    lt = get_object_or_404(LensType, pk=pk)
    lt.is_active = not lt.is_active
    lt.save()
    if request.headers.get('HX-Request'):
        types = LensType.objects.all().order_by('name')
        response = render(request, 'settings/lens_type_list.html#lens_type_table', {'types': types})
        status = 'activated' if lt.is_active else 'deactivated'
        response['HX-Trigger'] = json.dumps({'show-message': {'text': f'Lens type {status}.', 'type': 'success'}})
        return response
    return redirect('lens-type-list')

@login_required
def dashboard(request):
    patients = Patient.objects.all().order_by('-created_at')
    total_patients = patients.count()
    new_patients_today = Patient.objects.filter(created_at__date=date.today()).count()
    orders_in_production = Patient.objects.filter(status='In Production').count()
    ready_count = Patient.objects.filter(status='Ready').count()
    recent = patients[:8]
    return render(request, 'dashboard.html', {
        'total_patients': total_patients,
        'new_patients_today': new_patients_today,
        'orders_in_production': orders_in_production,
        'ready_count': ready_count,
        'recent_patients': recent,
    })

@login_required
def patient_table(request):
    query = request.GET.get('q', '')
    gender = request.GET.get('gender', 'all')
    status = request.GET.get('status', 'all')
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    per_page = 8

    patients = Patient.objects.all().order_by('-created_at')
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    if gender != 'all':
        patients = patients.filter(gender=gender)
    if status != 'all':
        patients = patients.filter(status=status)

    total = patients.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_data = patients[start:start + per_page]

    return render(request, 'dashboard.html#patient_table', {
        'patients': page_data,
        'page': page,
        'total_pages': total_pages,
        'query': query,
        'gender_filter': gender,
        'status_filter': status,
    })

@login_required
def patient_form(request, pk=None):
    patient = get_object_or_404(Patient, pk=pk) if pk else None
    legend = 'Edit Patient' if pk else 'Add New Patient'

    if request.method == 'POST':
        post_data = request.POST.copy()
        if not pk:
            post_data.setdefault('status', 'Consultation')
            post_data.setdefault('last_visit', date.today().isoformat())
        form = PatientForm(post_data, instance=patient)
        if form.is_valid():
            p = form.save(commit=False)
            if not pk:
                p.status = 'Consultation'
            p.updated_by = request.user
            p.save()
            last_rx = p.prescription_history.first()
            if (not last_rx
                or last_rx.prescription_od != p.prescription_od
                or last_rx.prescription_os != p.prescription_os
                or last_rx.lens_type_id != p.lens_type_id):
                PrescriptionRecord.objects.create(
                    patient=p,
                    prescription_od=p.prescription_od,
                    prescription_os=p.prescription_os,
                    lens_type=p.lens_type,
                    notes=p.notes,
                    updated_by=request.user,
                )
            if request.headers.get('HX-Request'):
                patients = Patient.objects.all().order_by('-created_at')
                response = render(request, 'dashboard.html#patient_table', {
                    'patients': patients,
                    'page': 1,
                    'total_pages': max(1, (patients.count() + 7) // 8),
                    'query': '',
                    'gender_filter': 'all',
                    'status_filter': 'all',
                })
                response['HX-Trigger'] = json.dumps({
                    'show-message': {'text': 'Patient saved successfully.', 'type': 'success'},
                    'refreshDashboardRecent': True,
                })
                return response
            return redirect('/')
        if request.headers.get('HX-Request'):
            response = render(request, 'dashboard.html#patient_form', {
                'form': form,
                'patient': patient,
                'legend': legend,
            })
            response['HX-Retarget'] = '#modal-container'
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Please correct the errors below.', 'type': 'error'}})
            return response
    else:
        form = PatientForm(instance=patient)

    if request.headers.get('HX-Request'):
        return render(request, 'dashboard.html#patient_form', {
            'form': form,
            'patient': patient,
            'legend': legend,
        })
    return render(request, 'dashboard.html', {
        'form': form,
        'patient': patient,
        'legend': legend,
    })

@login_required
def patient_detail(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    try:
        history = list(p.prescription_history.all()[:20])
    except OperationalError:
        history = []
    return render(request, 'partials/patient_detail.html', {
        'p': p,
        'history': history,
    })

@login_required
@require_POST
def patient_update_status(request, pk):
    p = get_object_or_404(Patient, pk=pk)
    status = request.POST.get('status')
    if status in dict(Patient.STATUS_CHOICES):
        p.status = status
        p.updated_by = request.user
        p.save(update_fields=['status', 'updated_by'])
    return render(request, 'partials/status_badge.html', {'p': p})

@login_required
def patient_delete(request, pk):
    get_object_or_404(Patient, pk=pk).delete()
    patients = Patient.objects.all().order_by('-created_at')
    return render(request, 'dashboard.html#patient_table', {
        'patients': patients,
        'page': 1,
        'total_pages': max(1, (patients.count() + 7) // 8),
        'query': '',
        'gender_filter': 'all',
        'status_filter': 'all',
    })

@login_required
def dashboard_recent(request):
    recent = Patient.objects.all().order_by('-created_at')[:5]
    return render(request, 'dashboard.html#dashboard_recent', {
        'recent_patients': recent,
    })


@login_required
def patient_list(request):
    per_page = 8
    try:
        page = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page = 1
    patients = Patient.objects.all().order_by('-created_at')
    total = patients.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_data = patients[start:start + per_page]
    return render(request, 'patient_list.html', {
        'patients': page_data,
        'page': page,
        'total_pages': total_pages,
        'query': '',
        'gender_filter': 'all',
        'status_filter': 'all',
    })

@login_required
def appointments(request):
    return render(request, 'page_unavailable.html', {
        'title': 'Appointments',
        'subtitle': 'Schedule and manage patient appointments',
        'icon': '<svg class="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
    })

@login_required
def inventory(request):
    return render(request, 'page_unavailable.html', {
        'title': 'Inventory',
        'subtitle': 'Track frames, lenses, and supplies',
        'icon': '<svg class="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>',
    })

@login_required
def billing(request):
    return render(request, 'page_unavailable.html', {
        'title': 'Billing',
        'subtitle': 'Manage invoices and payments',
        'icon': '<svg class="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
    })


@login_required
def backup_index(request):
    db_path = settings.DATABASES['default']['NAME']
    stats = {}
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        stats['size'] = size
        stats['size_display'] = _format_size(size)
    stats['last_modified'] = datetime.now()
    stats['patient_count'] = Patient.objects.count()
    stats['lens_type_count'] = LensType.objects.count()
    stats['staff_count'] = User.objects.filter(is_superuser=False).count()
    return render(request, 'settings/backup.html', {'stats': stats})


def _format_size(bytes_count):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"


@login_required
def backup_download(request):
    db_path = settings.DATABASES['default']['NAME']
    if not os.path.exists(db_path):
        return redirect('backup-index')
    today = datetime.now().strftime('%Y-%m-%d')
    return FileResponse(open(db_path, 'rb'), as_attachment=True, filename=f'opticare-backup-{today}.sqlite3')


@login_required
@require_POST
def backup_restore(request):
    if 'backup_file' not in request.FILES:
        response = HttpResponse()
        response['HX-Trigger'] = json.dumps({'show-message': {'text': 'No file selected.', 'type': 'error'}})
        response['HX-Redirect'] = reverse('backup-index')
        return response

    uploaded = request.FILES['backup_file']

    if uploaded.size > 100 * 1024 * 1024:
        response = HttpResponse()
        response['HX-Trigger'] = json.dumps({'show-message': {'text': 'File too large (max 100 MB).', 'type': 'error'}})
        response['HX-Redirect'] = reverse('backup-index')
        return response

    header = uploaded.read(16)
    uploaded.seek(0)
    if header[:16] != b'SQLite format 3\0':
        response = HttpResponse()
        response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Invalid file: not a valid SQLite database.', 'type': 'error'}})
        response['HX-Redirect'] = reverse('backup-index')
        return response

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
    try:
        for chunk in uploaded.chunks():
            tmp.write(chunk)
        tmp.close()

        try:
            conn = sqlite3.connect(tmp.name)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_patient'")
            if not cursor.fetchone():
                conn.close()
                os.unlink(tmp.name)
                response = HttpResponse()
                response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Invalid backup: missing patient data.', 'type': 'error'}})
                response['HX-Redirect'] = reverse('backup-index')
                return response
            conn.close()
        except sqlite3.DatabaseError:
            os.unlink(tmp.name)
            response = HttpResponse()
            response['HX-Trigger'] = json.dumps({'show-message': {'text': 'Corrupted backup file.', 'type': 'error'}})
            response['HX-Redirect'] = reverse('backup-index')
            return response

        db_path = settings.DATABASES['default']['NAME']
        timestamp = datetime.now().strftime('%Y-%m-%dT%H%M%S')
        auto_backup = str(db_path) + f'.auto-{timestamp}'
        shutil.copy2(db_path, auto_backup)

        from django.db import connection
        connection.ensure_connection()
        src_conn = sqlite3.connect(tmp.name)
        src_conn.backup(connection.connection, pages=-1)
        src_conn.close()
        connection.close()

        os.unlink(tmp.name)

        response = HttpResponse()
        response['HX-Trigger'] = json.dumps({
            'show-message': {'text': f'Backup restored. Previous DB saved as {os.path.basename(auto_backup)}.', 'type': 'success'}
        })
        response['HX-Redirect'] = reverse('backup-index')
        return response
    except Exception as e:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        response = HttpResponse()
        response['HX-Trigger'] = json.dumps({'show-message': {'text': f'Restore failed: {str(e)}', 'type': 'error'}})
        response['HX-Redirect'] = reverse('backup-index')
        return response