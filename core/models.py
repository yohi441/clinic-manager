from datetime import date
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('optometrist', 'Optometrist'),
        ('staff', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

class LensType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class PrescriptionRecord(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='prescription_history')
    prescription_od = models.CharField(max_length=100, blank=True, default='')
    prescription_os = models.CharField(max_length=100, blank=True, default='')
    lens_type = models.ForeignKey(LensType, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Rx for {self.patient} ({self.created_at.date()})"

class Patient(models.Model):
    STATUS_CHOICES = [
        ('Consultation', 'Consultation'),
        ('Fitting', 'Fitting'),
        ('In Production', 'In Production'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    contact = models.CharField(max_length=50)
    prescription_od = models.CharField(max_length=100, blank=True, default='')
    prescription_os = models.CharField(max_length=100, blank=True, default='')
    lens_type = models.ForeignKey(
        LensType, on_delete=models.SET_NULL, null=True, blank=True
    )
    address = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Consultation')
    last_visit = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class ClinicSetting(models.Model):
    clinic_name = models.CharField(max_length=200, default='Eye Clinic')

    class Meta:
        verbose_name = 'Clinic Setting'
        verbose_name_plural = 'Clinic Settings'

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.clinic_name
