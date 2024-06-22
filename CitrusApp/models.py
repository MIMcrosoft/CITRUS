from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

DIVISION_CHOICES = [
    ("Pamplemousse", "Pamplemousse"),
    ("Tangerine", "Tangerine"),
    ("Clementine", "Clementine")
]

SESSION_CHOICES = [
    ("Automne","Automne"),
    ("Hiver","Hiver")
]
class Saison(models.Model):
    saison_id = models.AutoField(primary_key=True)
    nom_saison = models.CharField(max_length=255)

    calendrier_officiel_id = models.ForeignKey('Calendrier', on_delete=models.CASCADE)

class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    nom_session = models.CharField(max_length=50)
    type = models.CharField(max_length=25, choices=SESSION_CHOICES)

    saison_id = models.ForeignKey(Saison, on_delete=models.CASCADE)

class Serie(models.Model):
    serie_id = models.AutoField(primary_key=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)

    saison_id = models.ForeignKey(Saison, on_delete=models.CASCADE)

class Calendrier(models.Model):
    calendrier_id = models.AutoField(primary_key=True)
    nom_calendrier = models.CharField(max_length=50)
    nb_match = models.IntegerField()

    saison_id = models.ForeignKey(Saison, on_delete=models.CASCADE)

class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    nom_college = models.CharField(max_length=100, unique=True)
    locationX = models.FloatField()
    locationY = models.FloatField()
    adresse = models.CharField(max_length=255)

class Interprete(models.Model):
    interprete_id = models.AutoField(primary_key=True)
    nom_interprete = models.CharField(max_length=100)
    prenom_interprete = models.CharField(max_length=100)
    pronom_interprete = models.CharField(max_length=20, blank=True, null=True)
    numero_interprete = models.CharField(max_length=20, blank=True, null=True)
    role_interprete = models.CharField(max_length=1, blank=True, null=True)

    equipes = models.ManyToManyField('Equipe')

class Equipe(models.Model):
    id_equipe = models.AutoField(primary_key=True)
    nom_equipe = models.CharField(max_length=100,unique=True)
    url_logo = models.URLField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)
    last_modified = models.DateTimeField(auto_now=True)

    college_id = models.ForeignKey(College, on_delete=models.CASCADE)
    interpretes = models.ManyToManyField(Interprete)
    matchs = models.ManyToManyField('Match')

class CoachManager(BaseUserManager):
    def create_user(self, courriel, password=None, **extra_fields):
        if not courriel:
            raise ValueError("Le courriel n'existe pas")
        courriel = self.normalize_email(courriel)
        user = self.model(courriel=courriel, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, courriel, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(courriel, password, **extra_fields)

class Coach(AbstractUser):
    coach_id = models.AutoField(primary_key=True)
    nom_coach = models.CharField(max_length=100)
    prenom_coach = models.CharField(max_length=100)
    courriel = models.EmailField(max_length=255, unique=True)
    admin_flag = models.BooleanField(default=False)
    equipe_id = models.ForeignKey(Equipe, on_delete=models.CASCADE, null=True, blank=True)
    objects = CoachManager()

    USERNAME_FIELD = 'courriel'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.courriel

    @property
    def is_admin(self):
        return self.admin_flag
class Punition(models.Model):
    punition_id = models.AutoField(primary_key=True)
    nom_punition = models.CharField(max_length=50)
    est_majeure = models.BooleanField(default=False)

class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    score_eq1 = models.IntegerField(default=0)
    score_eq2 = models.IntegerField(default=0)
    etoile1 = models.CharField(max_length=255,blank=True, null=True)
    etoile2 = models.CharField(max_length=255,blank=True, null=True)
    etoile3 = models.CharField(max_length=255,blank=True, null=True)
    etoile4 = models.CharField(max_length=255,blank=True, null=True)
    nom_arbitre = models.CharField(max_length=100,blank=True, null=True)
    url_photo = models.URLField(blank=True, null=True)

    session_id = models.ForeignKey(Session, on_delete=models.CASCADE)
    serie_id = models.ForeignKey(Serie, on_delete=models.CASCADE)
    equipe1_id = models.ForeignKey(Equipe, on_delete=models.CASCADE,related_name='equipe_hote')
    equipe2_id = models.ForeignKey(Equipe, on_delete=models.CASCADE,related_name='equipe_visiteure')
    calendrier_id = models.ForeignKey(Calendrier, on_delete=models.CASCADE)
    punitions = models.ManyToManyField(Punition)



