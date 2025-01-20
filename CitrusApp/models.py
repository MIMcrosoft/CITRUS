from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from googlemaps import geocoding, Client
import segno
from .NOTPUBLIC import API_KEY, EMAIL_PSWD
from datetime import datetime, timedelta
from io import BytesIO
import base64
import hashlib
import locale
from django.conf import settings


def hash_code(code: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Encode the string and update the hash object
    hash_object.update(code.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex


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
    est_active = models.BooleanField(default=False)

    calendrier_officiel = models.ForeignKey('Calendrier', on_delete=models.CASCADE, null=True)

    @classmethod
    def createSaison(cls, nom_saison):
        saison = cls(
            nom_saison=nom_saison
        )
        saison.save()
        for equipe in Equipe.objects.all():
            alignements = Alignements.create_alignement(equipe, saison)
            alignements.save()

        return saison

    def set_active(self):
        if self.est_active == False:
            for saison in Saison.objects.all():
                saison.est_active = False
            self.est_active = True

    def __str__(self):
        return self.nom_saison


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

    def __str__(self):
        return self.saison.nom_saison + "-SERIE-" + str(self.division)


class Calendrier(models.Model):
    calendrier_id = models.AutoField(primary_key=True)
    nom_calendrier = models.CharField(max_length=50)
    nb_match = models.IntegerField(default=0)

    saison_officiel = models.ForeignKey(Saison, on_delete=models.CASCADE, null=True)

    @classmethod
    def createCalendrier(cls, annee, dateDepartAut, dateDepartHiv, version, nbSemaineAut, nbSemaineHiv):
        calendrier = cls(
            nom_calendrier=annee + "_V" + version
        )
        calendrier.save()

        sessionAut = Session.createSession("AUT", "Automne", nbSemaineAut, calendrier.calendrier_id)
        sessionHiv = Session.createSession("HIV", "Hiver", nbSemaineHiv, calendrier.calendrier_id)

        def next_wednesday(current_date):
            # Calculate how many days to add to reach the next Wednesday
            days_ahead = 2 - current_date.weekday()  # Wednesday is 2 (Monday is 0)
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            return current_date + timedelta(days=days_ahead)

        # Example usage
        dateAut = datetime.strptime(dateDepartAut, '%Y-%m-%d').date()
        dateHiv = datetime.strptime(dateDepartHiv, '%Y-%m-%d').date()

        # Loop for the autumn session
        for i in range(nbSemaineAut):
            semaine = Semaine.createSemaine(session_id=sessionAut.session_id, date=dateAut)
            dateAut = next_wednesday(dateAut)

        # Loop for the winter session
        for i in range(nbSemaineHiv):
            semaine = Semaine.createSemaine(session_id=sessionHiv.session_id, date=dateHiv)
            dateHiv = next_wednesday(dateHiv)
        return calendrier

    def __str__(self):
        return self.nom_calendrier


class Semaine(models.Model):
    semaine_id = models.AutoField(primary_key=True)
    nb_match = models.IntegerField()
    date = models.DateField(blank=True, null=True)

    session = models.ForeignKey(Session, related_name="semaines", on_delete=models.CASCADE, null=True)

    @classmethod
    def createSemaine(cls, nb_match=0, date=None, session_id=None):
        semaine = cls(
            nb_match=nb_match,
            date=date,
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
    indisponibilites = models.JSONField(null=True, blank=True)

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
    pronom_interprete = models.CharField(max_length=20, blank=True, default="")
    numero_interprete = models.CharField(max_length=20, blank=True, default="")
    role_interprete = models.CharField(max_length=1, blank=True, null=True)

    alignement = models.ManyToManyField('Alignements', related_name='interpretes')

    @classmethod
    def createInterprete(cls, nom_interprete, pronom_interprete, numero_interprete, role_interprete,
                         alignement):
        interprete = cls(
            nom_interprete=nom_interprete,
            pronom_interprete=pronom_interprete,
            numero_interprete=numero_interprete,
            role_interprete=role_interprete
        )
        interprete.save()

        if alignement:
            interprete.alignement.add(alignement)
            interprete.save()
            alignement.save()

        return interprete

    def get_equipe(self, saison):

        equipes = [alignement.equipe for alignement in self.alignement.all() if alignement.saison == saison]

        if len(equipes) > 1:
            return None
        else:
            return equipes[0]

    def __str__(self):
        return f"{self.nom_interprete} #{self.numero_interprete} ({self.pronom_interprete})"


class Equipe(models.Model):
    id_equipe = models.AutoField(primary_key=True)
    nom_equipe = models.CharField(max_length=100, unique=True)
    logo = models.FileField(blank=True, null=True, upload_to='logos/')
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES)
    last_modified = models.DateTimeField(auto_now=True)
    nb_matchVis = models.IntegerField(default=0)
    nb_matchHost = models.IntegerField(default=0)
    indisponibilites = models.JSONField(null=True, blank=True)

    college = models.ForeignKey(College, related_name="equipes", on_delete=models.CASCADE, null=True)
    alignements = models.ForeignKey('Alignements', related_name="alignements", on_delete=models.SET_NULL, null=True,
                                    blank=True)
    matchs = models.ManyToManyField('Match', null=True, blank=True)

    @classmethod
    def createEquipe(cls, nomEquipe, logo=None, division=None, college=None):
        equipe = cls(
            nom_equipe=nomEquipe,
            logo=logo,
            division=division,
            college=college,
        )
        equipe.save()
        return equipe

    def getAlignement(self, saisonID):
        selectedSaison = Saison.objects.filter(saison_id=saisonID).first()
        alignement = Alignements.objects.filter(saison=selectedSaison, equipe=self).first().interpretes.all()
        print(Alignements.objects.filter(saison=selectedSaison, equipe=self).first().interpretes.all())
        return Alignements.objects.filter(saison=selectedSaison, equipe=self).first().interpretes.all()

    def getUrlPhoto(self):
        if settings.DEBUG:
            domain = "http://localhost:8000/Citrus"
        else:
            domain = "https://citrus.liguedespamplemousses.com"

        if self.logo and self.logo.url :
            return domain + self.logo.url
        else :
            return None



    def __str__(self):
        return self.nom_equipe


class Alignements(models.Model):
    id_alignement = models.AutoField(primary_key=True)

    equipe = models.ForeignKey(Equipe, related_name="equipe", on_delete=models.CASCADE, null=False)
    saison = models.ForeignKey(Saison, related_name="saison", on_delete=models.CASCADE, null=False)

    @classmethod
    def create_alignement(cls, equipe, saison):
        alignement = cls(
            equipe=equipe,
            saison=saison
        )
        alignement.save()
        return alignement

    def __str__(self):
        return self.saison.nom_saison + "-" + self.equipe.nom_equipe


class CoachManager(BaseUserManager):
    def create_user(self, prenom_coach, nom_coach, pronom_coach, courriel, password=None, equipe=None, **extra_fields):
        if not courriel:
            raise ValueError("Le courriel est obligatoire")
        courriel = self.normalize_email(courriel)
        user = self.model(
            prenom_coach=prenom_coach,
            nom_coach=nom_coach,
            pronom_coach=pronom_coach,
            courriel=courriel,
            equipe=equipe,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, prenom_coach, nom_coach, courriel, pronom_coach=None, password=None, equipe=None,
                         **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('admin_flag', True)

        return self.create_user(
            prenom_coach=prenom_coach,
            nom_coach=nom_coach,
            pronom_coach=pronom_coach,
            courriel=courriel,
            password=password,
            equipe=equipe,
            **extra_fields
        )


class Coach(AbstractUser):
    coach_id = models.AutoField(primary_key=True)
    nom_coach = models.CharField(max_length=100)
    prenom_coach = models.CharField(max_length=100)
    pronom_coach = models.CharField(max_length=20, blank=True, null=True)
    courriel = models.EmailField(max_length=255, unique=True)
    admin_flag = models.BooleanField(default=False)
    validated_flag = models.BooleanField(default=False)
    equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    objects = CoachManager()

    username = None

    college = models.ForeignKey('College', on_delete=models.SET_NULL, null=True, blank=True, related_name='college')

    USERNAME_FIELD = 'courriel'
    REQUIRED_FIELDS = ['prenom_coach', 'nom_coach']  # You can set other required fields here

    def __str__(self):
        return self.courriel

    @property
    def is_admin(self):
        return self.admin_flag


class Punition(models.Model):
    punition_id = models.AutoField(primary_key=True)
    nom_punition = models.CharField(max_length=50)
    est_majeure = models.BooleanField(default=False)

    equipe_punie = models.ForeignKey(Equipe, on_delete=models.DO_NOTHING, related_name='equipe_punie', null=True)
    @classmethod
    def createPunition(cls, nom_punition, est_majeure,equipePunie):
        punition = cls(
            nom_punition=nom_punition,
            est_majeure=est_majeure,
            equipe_punie=equipePunie
        )

        punition.save()
        return punition


class Match(models.Model):
    match_id = models.AutoField(primary_key=True)
    score_eq1 = models.IntegerField(default=0)
    score_eq2 = models.IntegerField(default=0)
    etoile1 = models.CharField(max_length=255, blank=True, null=True)
    etoile2 = models.CharField(max_length=255, blank=True, null=True)
    etoile3 = models.CharField(max_length=255, blank=True, null=True)
    etoile4 = models.CharField(max_length=255, blank=True, null=True)
    nom_arbitre = models.CharField(max_length=100, blank=True, null=True)
    date_match = models.DateTimeField(null=True, blank=True)
    url_photo = models.URLField(blank=True, null=True)
    division = models.CharField(max_length=50, choices=DIVISION_CHOICES, default=DIVISION_CHOICES[0][0])
    completed_flag = models.BooleanField(default=False)
    validated_flag = models.BooleanField(default=False)
    improvisations = models.CharField(max_length=1000, blank=True, null=True, default="[]")
    cache = models.CharField(max_length=5000, blank=True, null=True)

    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, null=True,blank=True)
    equipe1 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_hote', null=True)
    equipe2 = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='equipe_visiteure', null=True)
    semaine = models.ForeignKey(Semaine, related_name="matchs", on_delete=models.SET_NULL, null=True)
    punitions = models.ManyToManyField(Punition,blank=True,related_name='punitions', null=True)

    @classmethod
    def validate_match(self):
        pass

    @classmethod
    def createMatch(cls, division, session=None, serie=None, equipe1=None, equipe2=None, semaine=None, date_match=None):
        match = cls(
            session=session,
            serie=serie,
            equipe1=equipe1,
            equipe2=equipe2,
            semaine=semaine,
            division=division,
            date_match=date_match
        )
        equipe1.nb_matchHost += 1
        equipe2.nb_matchVis += 1

        equipe1.save()
        equipe2.save()

        code = str(equipe1.nom_equipe) + str(equipe2.nom_equipe) + str(match.match_id)
        match.url_match = "http://localhost:8000/Citrus/match-" + hash_code(code)

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

    @property
    def get_urlMatch(self):
        code = str(self.equipe1.nom_equipe) + str(self.equipe2.nom_equipe) + str(self.match_id)
        if settings.DEBUG:
            self.url_match = "http://localhost:8000/Citrus/Match-" + hash_code(code)
        else:
            self.url_match = "https://citrus.liguedespamplemousses.com/Citrus/Match-" + hash_code(code)
        self.save()
        return self.url_match
    def get_QrCode(self):
        qr = segno.make(self.get_urlMatch)

        buffer = BytesIO()
        qr.save(buffer, kind='png', scale=7)
        buffer.seek(0)

        imageBase64 = base64.b64encode(buffer.read()).decode('utf-8')

        return f"data:image/png;base64,{imageBase64}"

    def get_dateFormatted(self):
        #locale.setlocale(locale.LC_TIME, 'en_US')

        date_formatted = self.date_match.strftime("%d %b")
        return date_formatted

    def get_dateFormattedWithYear(self):
        #locale.setlocale(locale.LC_TIME, 'en_US')
        date_formatted = self.date_match.strftime("%d %b %Y")

        return date_formatted

    def __str__(self):
        date_formatted = self.date_match.strftime("%Y-%m-%d")
        session = self.session
        equipe1 = self.equipe1
        equipe2 = self.equipe2

        type = session.type if session else "SERIE"

        return str(date_formatted) + " - " + type + " - " + equipe2.nom_equipe + " VS " + equipe1.nom_equipe
