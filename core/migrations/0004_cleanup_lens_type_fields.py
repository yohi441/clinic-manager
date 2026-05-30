from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_populate_lens_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='patient',
            name='lens_type',
        ),
        migrations.RenameField(
            model_name='patient',
            old_name='lens_type_fk',
            new_name='lens_type',
        ),
    ]
