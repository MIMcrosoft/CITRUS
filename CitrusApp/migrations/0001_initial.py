# Generated by Django 4.2.13 on 2024-06-02 03:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Calendrier',
            fields=[
                ('calendrier_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_calendrier', models.CharField(max_length=50)),
                ('nb_match', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='College',
            fields=[
                ('college_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_college', models.CharField(max_length=100, unique=True)),
                ('locationX', models.FloatField()),
                ('locationY', models.FloatField()),
                ('adresse', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Equipe',
            fields=[
                ('id_equipe', models.AutoField(primary_key=True, serialize=False)),
                ('nom_equipe', models.CharField(max_length=100, unique=True)),
                ('url_logo', models.URLField(blank=True, max_length=255, null=True)),
                ('division', models.CharField(choices=[('Pamplemousse', 'Pamplemousse'), ('Tangerine', 'Tangerine'), ('Clementine', 'Clementine')], max_length=50)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('college_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.college')),
            ],
        ),
        migrations.CreateModel(
            name='Punition',
            fields=[
                ('punition_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_punition', models.CharField(max_length=50)),
                ('est_majeure', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Saison',
            fields=[
                ('saison_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_saison', models.CharField(max_length=255)),
                ('calendrier_officiel_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.calendrier')),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('session_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_session', models.CharField(max_length=50)),
                ('type', models.CharField(choices=[('Automne', 'Automne'), ('Hiver', 'Hiver')], max_length=25)),
                ('saison_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.saison')),
            ],
        ),
        migrations.CreateModel(
            name='Serie',
            fields=[
                ('serie_id', models.AutoField(primary_key=True, serialize=False)),
                ('division', models.CharField(choices=[('Pamplemousse', 'Pamplemousse'), ('Tangerine', 'Tangerine'), ('Clementine', 'Clementine')], max_length=50)),
                ('saison_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.saison')),
            ],
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('match_id', models.AutoField(primary_key=True, serialize=False)),
                ('score_eq1', models.IntegerField(default=0)),
                ('score_eq2', models.IntegerField(default=0)),
                ('etoile1', models.CharField(blank=True, max_length=255, null=True)),
                ('etoile2', models.CharField(blank=True, max_length=255, null=True)),
                ('etoile3', models.CharField(blank=True, max_length=255, null=True)),
                ('etoile4', models.CharField(blank=True, max_length=255, null=True)),
                ('nom_arbitre', models.CharField(blank=True, max_length=100, null=True)),
                ('url_photo', models.URLField(blank=True, null=True)),
                ('calendrier_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.calendrier')),
                ('equipe1_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipe_hote', to='CitrusApp.equipe')),
                ('equipe2_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipe_visiteure', to='CitrusApp.equipe')),
                ('punitions', models.ManyToManyField(to='CitrusApp.punition')),
                ('serie_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.serie')),
                ('session_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.session')),
            ],
        ),
        migrations.CreateModel(
            name='Interprete',
            fields=[
                ('interprete_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_interprete', models.CharField(max_length=100)),
                ('prenom_interprete', models.CharField(max_length=100)),
                ('pronom_interprete', models.CharField(blank=True, max_length=20, null=True)),
                ('numero_interprete', models.CharField(blank=True, max_length=20, null=True)),
                ('role_interprete', models.CharField(blank=True, max_length=1, null=True)),
                ('equipes', models.ManyToManyField(to='CitrusApp.equipe')),
            ],
        ),
        migrations.AddField(
            model_name='equipe',
            name='interpretes',
            field=models.ManyToManyField(to='CitrusApp.interprete'),
        ),
        migrations.AddField(
            model_name='equipe',
            name='matchs',
            field=models.ManyToManyField(to='CitrusApp.match'),
        ),
        migrations.CreateModel(
            name='Coach',
            fields=[
                ('coach_id', models.AutoField(primary_key=True, serialize=False)),
                ('nom_coach', models.CharField(max_length=100)),
                ('prenom_coach', models.CharField(max_length=100)),
                ('courriel', models.EmailField(max_length=255)),
                ('mdp', models.CharField(max_length=255)),
                ('admin_flag', models.BooleanField(default=False)),
                ('equipe_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.equipe')),
            ],
        ),
        migrations.AddField(
            model_name='calendrier',
            name='saison_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='CitrusApp.saison'),
        ),
    ]