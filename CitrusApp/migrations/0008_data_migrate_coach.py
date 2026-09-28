from django.db import migrations


def migrate_coach_to_coachs(apps, schema_editor):
    Alignement = apps.get_model('CitrusApp', 'Alignement')
    for alignement in Alignement.objects.filter(coach__isnull=False):
        alignement.coachs.add(alignement.coach)


class Migration(migrations.Migration):

    dependencies = [
        ('CitrusApp', '0007_remove_alignement_coach_alignement_coachs'),
    ]

    operations = [
        migrations.RunPython(migrate_coach_to_coachs, migrations.RunPython.noop),
    ]