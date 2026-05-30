from datetime import date
from django.db import migrations


def backfill_dob(apps, schema_editor):
    Patient = apps.get_model('core', 'Patient')
    today = date.today()
    for p in Patient.objects.filter(date_of_birth__isnull=True):
        p.date_of_birth = date(today.year - p.age, 1, 1)
        p.save(update_fields=['date_of_birth'])


def reverse_func(apps, schema_editor):
    Patient = apps.get_model('core', 'Patient')
    Patient.objects.update(date_of_birth=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_patient_date_of_birth'),
    ]

    operations = [
        migrations.RunPython(backfill_dob, reverse_func),
    ]
