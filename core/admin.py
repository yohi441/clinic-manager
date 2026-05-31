from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import ClinicSetting, LensType, Patient, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class CustomUserAdmin(UserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(LensType)
class LensTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass

@admin.register(ClinicSetting)
class ClinicSettingAdmin(admin.ModelAdmin):
    pass
