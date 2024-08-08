from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from googlemaps import geocoding, Client
from .NOTPUBLIC import API_KEY, GMAIL_KEY

DIVISION_CHOICES = [
    ("Pamplemousse", "Pamplemousse"),
    ("Tangerine", "Tangerine"),
    ("Clementine", "Clementine")
]

SESSION_CHOICES = [
    ("Automne", "Automne"),
    ("Hiver", "Hiver")
]


class Saison(models.Model):
    saison_id = models.AutoField(primary_key=True)
    nom_saison = models.CharField(max_length=255)

    calendrier_officiel = models.ForeignKey('Calendrier', on_delete=models.CASCADE, null=True)


class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    nom_session = models.CharField(max_length=50)
    type = models.CharField(max_length=25, choices=SESSION_CHOICES)
    nb_semaine = models.IntegerField(default=10)

    saison = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)
    calendrier = models.ForeignKey('Calendrier', related_name='sessions', on_delete=models.CASCADE, null=True)

    @classmethod
    def createSession(cls, nom_session, type, nb_semaine=10, calendrier_id=None):
        session = cls(
            nom_session=nom_session,
            type=type,
            nb_semaine=nb_semaine,
            calendrier_id=calendrier_id
        )
        session.save()
        return session

    def __str__(self):
        return self.calendrier_id.__str__() + " - " + self.nom_session


class Serie(models.Model):
    serie_id = models.AutoField(primary_key=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)

    saison = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)


class Calendrier(models.Model):
    calendrier_id = models.AutoField(primary_key=True)
    nom_calendrier = models.CharField(max_length=50)
    nb_match = models.IntegerField(default=0)

    saison_officiel = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)

    @classmethod
    def createCalendrier(cls, annee, version, nbSemaineAut, nbSemaineHiv):
        calendrier = cls(
            nom_calendrier=annee + "_V" + version
        )
        calendrier.save()

        sessionAut = Session.createSession("AUT", "Automne", nbSemaineAut, calendrier.calendrier_id)
        sessionHiv = Session.createSession("HIV", "Hiver", nbSemaineHiv, calendrier.calendrier_id)

        for i in range(nbSemaineAut):
            semaine = Semaine.createSemaine(session_id=sessionAut.session_id)
        for i in range(nbSemaineHiv):
            semaine = Semaine.createSemaine(session_id=sessionHiv.session_id)
        return calendrier

    def __str__(self):
        return self.nom_calendrier


class Semaine(models.Model):
    semaine_id = models.AutoField(primary_key=True)
    nb_match = models.IntegerField()

    session = models.ForeignKey(Session, related_name="semaines", on_delete=models.CASCADE, null=True)

    @classmethod
    def createSemaine(cls, nb_match=0, session_id=None):
        semaine = cls(
            nb_match=nb_match,
            session_id=session_id
        )
        semaine.save()
        return semaine

    def __str__(self):
        session = Session.objects.get(session_id=self.session_id)
        return session.__str__() + " - " + str(self.semaine_id)


class College(models.Model):
    college_id = models.AutoField(primary_key=True)
    nom_college = models.CharField(max_length=100, unique=True)
    locationX = models.FloatField()
    locationY = models.FloatField()
    adresse = models.CharField(max_length=255)

    @classmethod
    def createCollege(cls, nom_college, adresse):

        gmaps = Client(key=API_KEY)

        try:
            geocode_result = geocoding.geocode(gmaps, adresse)

            if geocode_result and geocode_result[0]["geometry"]["location"]:
                locationX = geocode_result[0]["geometry"]["location"]["lat"]
                locationY = geocode_result[0]["geometry"]["location"]["lng"]

                college = cls(
                    nom_college=nom_college,
                    locationX=locationX,
                    locationY=locationY
                )
                college.save()
                return college
        except Exception as e:
            print(f"L'adresse n'a pas été trouvé : {e}")
            return None

    def __str__(self):
        return self.nom_college


class Interprete(models.Model):
    interprete_id = models.AutoField(primary_key=True)
    nom_interprete = models.CharField(max_length=100)
    prenom_interprete = models.CharField(max_length=100)
    pronom_interprete = models.CharField(max_length=20, blank=True, null=True)
    numero_interprete = models.CharField(max_length=20, blank=True, null=True)
    role_interprete = models.CharField(max_length=1, blank=True, null=True)

    equipes = models.ManyToManyField('Equipe')

    @classmethod
    def createInterprete(cls, nom_interprete, prenom_interprete, pronom_interprete, numero_interprete, role_interprete,
                         equipesIds):
        interprete = cls(
            nom_interprete=nom_interprete,
            prenom_interprete=prenom_interprete,
            pronom_interprete=pronom_interprete,
            numero_interprete=numero_interprete,
            role_interprete=role_interprete
        )
        interprete.save()
        for equipeID in equipesIds:
            equipe = Equipe.objects.get(id_equipe=equipeID)
            interprete.equipes.add(equipe)

        return interprete

    def __str__(self):
        return self.prenom_interprete + " " + self.nom_interprete + " #" + str(
            self.numero_interprete) + " (" + self.prenom_interprete + ")"


class Equipe(models.Model):
    id_equipe = models.AutoField(primary_key=True)
    nom_equipe = models.CharField(max_length=100, unique=True)
    url_logo = models.URLField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)
    last_modified = models.DateTimeField(auto_now=True)
    nb_matchVis = models.IntegerField(default=0)
    nb_matchHost = models.IntegerField(default=0)

    college = models.ForeignKey(College, related_name="equipes", on_delete=models.CASCADE, null=True)
    interpretes = models.ManyToManyField(Interprete, null=True,blank=True)
    matchs = models.ManyToManyField('Match', null=True,blank=True)

    @classmethod
    def createEquipe(cls, nomEquipe, url_logo=None, division=None, collegeID=None):
        equipe = cls(
            nomEquipe=nomEquipe,
            url_logo=url_logo,
            division=division,
            college_id=collegeID
        )
        equipe.save()
        return equipe

    def __str__(self):
        return self.nom_equipe


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
    etoile1 = models.CharField(max_length=255, blank=True, null=True)
    etoile2 = models.CharField(max_length=255, blank=True, null=True)
    etoile3 = models.CharField(max_length=255, blank=True, null=True)
    etoile4 = models.CharField(max_length=255, blank=True, null=True)
    nom_arbitre = models.CharField(max_length=100, blank=True, null=True)
    date_match = models.DateTimeField(auto_now=True)
    url_photo = models.URLField(blank=True, null=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)

    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, null=True)
    equipe1 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_hote', null=True)
    equipe2 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_visiteure', null=True)
    semaine = models.ForeignKey(Semaine, related_name="matchs", on_delete=models.SET_NULL, null=True)
    punitions = models.ManyToManyField(Punition)

    @classmethod
    def createMatch(cls,division,session=None, serie=None, equipe1=None, equipe2=None, semaine=None,):
        match = cls(
            session=session,
            serie=serie,
            equipe1=equipe1,
            equipe2=equipe2,
            semaine=semaine,
            division=division
        )
        equipe1.nb_matchHost += 1
        equipe2.nb_matchVis += 1

        equipe1.save()
        equipe2.save()

        match.save()
        return match

    @classmethod
    def deleteMatch(cls, match_id):
        try:
            match = cls.objects.get(pk=match_id)
            match.equipe1.nb_matchHost -= 1
            match.equipe2.nb_matchVis -= 1

            match.equipe1.save()
            match.equipe2.save()

            match.delete()
            return True
        except cls.DoesNotExist:
            return False
    def __str__(self):
        date_formatted = self.date_match.strftime("%Y-%m-%d")
        session = self.session
        equipe1 = self.equipe1
        equipe2 = self.equipe2

        type = session.type if session else "SERIE"

        return str(date_formatted) + " - " + type + " - " + equipe2.nom_equipe + " VS " + equipe1.nom_equipe
