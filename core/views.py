from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from datetime import date
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import LensType, Patient
from .forms import PatientForm


def role_required(*roles):
    def check(user):
        return hasattr(user, 'profile') and user.profile.role in roles
    return user_passes_test(check)


@login_required
def staff_list(request):
    users = User.objects.select_related('profile').filter(is_superuser=False).order_by('username')
    return render(request, 'settings/staff_list.html', {'users': users})


@login_required
@require_POST
def staff_create(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    first_name = request.POST.get('first_name', '')
    last_name = request.POST.get('last_name', '')
    role = request.POST.get('role', 'staff')
    if username and password:
        user = User.objects.create_user(username=username, password=password,
                                        first_name=first_name, last_name=last_name)
        user.profile.role = role
        user.profile.save()
    return redirect('staff-list')


@login_required
def staff_edit(request, pk):
    u = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        u.first_name = request.POST.get('first_name', '')
        u.last_name = request.POST.get('last_name', '')
        u.username = request.POST.get('username', u.username)
        password = request.POST.get('password')
        if password:
            u.set_password(password)
        u.profile.role = request.POST.get('role', u.profile.role)
        u.save()
        u.profile.save()
        return redirect('staff-list')
    return render(request, 'settings/staff_edit.html', {'u': u})


@login_required
@require_POST
def staff_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    return redirect('staff-list')


@login_required
@require_POST
def staff_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        return redirect('staff-list')
    user.delete()
    return redirect('staff-list')


@login_required
@require_POST
def staff_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    password = request.POST.get('password')
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
    name = request.POST.get('name')
    if name:
        LensType.objects.get_or_create(name=name.strip())
    return redirect('lens-type-list')


@login_required
def lens_type_edit(request, pk):
    lt = get_object_or_404(LensType, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            lt.name = name.strip()
            lt.save()
        return redirect('lens-type-list')
    return render(request, 'settings/lens_type_edit.html', {'lt': lt})


@login_required
@require_POST
def lens_type_toggle(request, pk):
    lt = get_object_or_404(LensType, pk=pk)
    lt.is_active = not lt.is_active
    lt.save()
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
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            p = form.save(commit=False)
            if not pk:
                p.status = 'Consultation'
            p.updated_by = request.user
            p.save()
            if request.headers.get('HX-Request'):
                patients = Patient.objects.all().order_by('-created_at')
                return render(request, 'dashboard.html#patient_table', {
                    'patients': patients,
                    'page': 1,
                    'total_pages': max(1, (patients.count() + 7) // 8),
                    'query': '',
                    'gender_filter': 'all',
                    'status_filter': 'all',
                })
            return redirect('/')
        if request.headers.get('HX-Request'):
            response = render(request, 'dashboard.html#patient_form', {
                'form': form,
                'patient': patient,
                'legend': legend,
            })
            response['HX-Retarget'] = '#modal-container'
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
    return render(request, 'dashboard.html#patient_detail', {
        'p': p,
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