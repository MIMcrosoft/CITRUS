from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('CitrusApp', '0008_data_migrate_coach'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='alignement',
            name='coach',
        ),
    ]