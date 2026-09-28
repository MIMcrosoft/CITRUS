from django.db import migrations


def backfill_division_et_statut(apps, schema_editor):
    Alignement = apps.get_model('CitrusApp', 'Alignement')
    for alignement in Alignement.objects.select_related('equipe').all():
        alignement.division = alignement.equipe.division
        alignement.est_active = alignement.equipe.est_active
        alignement.save(update_fields=['division', 'est_active'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('CitrusApp', '0010_equipe_division_saison'),
    ]

    operations = [
        migrations.RunPython(backfill_division_et_statut, noop),
    ]
