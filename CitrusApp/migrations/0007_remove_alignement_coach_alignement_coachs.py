from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('CitrusApp', '0006_remove_equipe_alignement_remove_equipe_matchs_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='alignement',
            name='coachs',
            field=models.ManyToManyField(blank=True, related_name='alignements', to=settings.AUTH_USER_MODEL),
        ),
    ]