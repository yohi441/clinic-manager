from django.db import migrations

LENS_CHOICES = [
    'Single Vision',
    'Progressive',
    'Bifocal',
    'Blue Light',
    'Photochromic',
    'High Index',
]

def populate_lens_types(apps, schema_editor):
    LensType = apps.get_model('core', 'LensType')
    Patient = apps.get_model('core', 'Patient')

    for name in LENS_CHOICES:
        LensType.objects.get_or_create(name=name)

    extra = Patient.objects.exclude(lens_type='').values_list('lens_type', flat=True).distinct()
    for name in extra:
        if name not in LENS_CHOICES:
            LensType.objects.get_or_create(name=name)

    for patient in Patient.objects.exclude(lens_type=''):
        try:
            patient.lens_type_fk = LensType.objects.get(name=patient.lens_type)
            patient.save(update_fields=['lens_type_fk'])
        except LensType.DoesNotExist:
            pass

def reverse_func(apps, schema_editor):
    LensType = apps.get_model('core', 'LensType')
    Patient = apps.get_model('core', 'Patient')
    Patient.objects.update(lens_type_fk=None)
    LensType.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_lenstype_patient_lens_type_fk'),
    ]

    operations = [
        migrations.RunPython(populate_lens_types, reverse_func),
    ]
