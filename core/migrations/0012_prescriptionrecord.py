from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_patient_updated_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrescriptionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prescription_od', models.CharField(blank=True, default='', max_length=100)),
                ('prescription_os', models.CharField(blank=True, default='', max_length=100)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lens_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.lenstype')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prescription_history', to='core.patient')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='auth.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunSQL(
            sql="""
                INSERT INTO core_prescriptionrecord
                    (prescription_od, prescription_os, lens_type_id, notes, patient_id, updated_by_id, created_at)
                SELECT
                    p.prescription_od,
                    p.prescription_os,
                    p.lens_type_id,
                    p.notes,
                    p.id,
                    p.updated_by_id,
                    COALESCE(p.updated_at, p.created_at, CURRENT_TIMESTAMP)
                FROM core_patient p
                WHERE p.prescription_od != '' OR p.prescription_os != '' OR p.lens_type_id IS NOT NULL;
            """,
            reverse_sql="""
                DELETE FROM core_prescriptionrecord;
            """,
        ),
    ]
