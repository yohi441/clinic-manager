from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('patients/table/', views.patient_table, name='patient-table'),
    path('patients/form/', views.patient_form, name='patient-create'),
    path('patients/form/<int:pk>/', views.patient_form, name='patient-edit'),
    path('patients/<int:pk>/detail/', views.patient_detail, name='patient-detail'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient-delete'),
    path('patients/<int:pk>/status/', views.patient_update_status, name='patient-status'),
    path('dashboard/recent/', views.dashboard_recent, name='dashboard-recent'),
    path('patients/list/', views.patient_list, name='patient-list'),
    path('staff/', views.role_required('admin')(views.staff_list), name='staff-list'),
    path('staff/create/', views.role_required('admin')(views.staff_create), name='staff-create'),
    path('staff/<int:pk>/toggle/', views.role_required('admin')(views.staff_toggle_active), name='staff-toggle'),
    path('staff/<int:pk>/edit/', views.role_required('admin')(views.staff_edit), name='staff-edit'),
    path('staff/<int:pk>/delete/', views.role_required('admin')(views.staff_delete), name='staff-delete'),
    path('staff/<int:pk>/reset-password/', views.role_required('admin')(views.staff_reset_password), name='staff-reset-password'),
    path('settings/lens-types/', views.role_required('admin', 'optometrist')(views.lens_type_list), name='lens-type-list'),
    path('settings/lens-types/create/', views.role_required('admin', 'optometrist')(views.lens_type_create), name='lens-type-create'),
    path('settings/lens-types/<int:pk>/edit/', views.role_required('admin', 'optometrist')(views.lens_type_edit), name='lens-type-edit'),
    path('settings/lens-types/<int:pk>/toggle/', views.role_required('admin', 'optometrist')(views.lens_type_toggle), name='lens-type-toggle'),
    path('appointments/', views.appointments, name='appointments'),
    path('inventory/', views.inventory, name='inventory'),
    path('billing/', views.billing, name='billing'),
]
