import ast
import random
import re
import smtplib
from calendar import Calendar
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from math import sqrt
import os
import django
from premailer import transform
import hashlib
from django.conf import settings
from pathlib import Path
from datetime import datetime
import segno
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CITRUS.settings')
django.setup()

from CitrusApp.admin import CoachCreationForm
from CitrusApp.NOTPUBLIC import EMAIL_PSWD
from CitrusApp.models import Calendrier, Session, Semaine, Match, College, Equipe, Coach, Saison
from enum import Enum, auto


class EmailType(Enum):
    INVITATION = auto()
    RESETPASSWORD = auto()
    VALIDATION = auto()


"""

"""


def hash_code(code: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Encode the string and update the hash object
    hash_object.update(code.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex

def sendCoachEmail(coachEmail, emailType: EmailType, coachCodeHash=""):
    smtp_server = 'node38-ca.n0c.com'
    smtp_port = 465
    sender_email = 'citrus@liguedespamplemousses.com'
    receiver_email = coachEmail
    password = EMAIL_PSWD

    base_dir = Path(__file__).resolve().parent

    domain = "http://localhost:8000" if settings.DEBUG else "https://citrus.liguedespamplemousses.com"

    if emailType == EmailType.INVITATION:
        coach = creationCompteCoach("UserTest", "UserTest", coachEmail, "IMPROMOMO8866887")
        urlSignIn = f"{domain}/Citrus/CoachSignIn/{coach.id}"
        with open("coachEmailInvite.html", 'r', encoding="utf-8") as file:
            html_body = file.read()
        html_bodyParam = html_body.replace("{urlSignIn}", urlSignIn)
        html_bodyParam_with_style = transform(html_bodyParam)

        subject = 'Invitation à la plateforme CITRUS'

    elif emailType == EmailType.RESETPASSWORD:
        template_path = base_dir / "templates" / "templatesCourriel" / "resetPasswordEmail.html"
        with open(template_path, 'r', encoding="utf-8") as file:
            html_body = file.read()
        urlResetPassword = f"{domain}/Citrus/ResetPassword-{coachCodeHash}"
        html_bodyParam = html_body.replace("{urlResetPassword}", urlResetPassword)
        html_bodyParam_with_style = transform(html_bodyParam)

        subject = 'Réinitialisation de ton mot de passe Citrus'

    elif emailType == EmailType.VALIDATION:
        template_path = base_dir / "templates" / "templatesCourriel" / "validationCompteEmail.html"
        with open(template_path, 'r', encoding="utf-8") as file:
            html_body = file.read()
        urlSignIn = f"{domain}/Citrus/Connexion/"
        html_bodyParam = html_body.replace("{urlSignIn}", urlSignIn)
        html_bodyParam_with_style = transform(html_bodyParam)

        subject = "Votre compte Citrus a été accepté par l'organisation!"

    else:
        raise ValueError(f"Type d'email non pris en charge: {emailType}")

    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_bodyParam_with_style, 'html'))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print('Le courriel à été envoyé avec succès')
    except Exception as e:
        print(f"Le courriel n'a pas été envoyé : {e}")



def creationCompteCoach(nomCoach, prenomCoach, courrielCoach, coachPwd):
    # Préparation des données du form
    data = {
        'nom_coach': nomCoach,
        'prenom_coach': prenomCoach,
        'courriel': courrielCoach,
        'password': coachPwd,
        'password2': coachPwd,
        'equipe_id': None,
        'admin_flag': False
    }

    # Création du form avec les données
    form = CoachCreationForm(data)

    if form.is_valid():
        coach = form.save()
        return coach
    else:
        # Handling des erreurs
        print(form.errors)
        return None


"""

"""


def fillCalendrier():
    """
    calculateDistance
    Description : Calcul la distance entre un college en paramètre et le reste des colleges de la base de données.
    Arguments : college1 (College) : college de référence avec qui les distances seront calculés.
                colleges (Liste de Colleges): Liste de Colleges avec lesquelles ont veut calculer la distance.
    Retour : distances (Liste de tuple)  : Liste des distances entre le college de référence et les colleges de la liste
            en suivant le format --> [(college, distance),...]
    """

    def calculateDistance(equipe):
        distances = []

        collegeRef = equipe.college
        for collegeAdv in College.objects.all():
            for equipeAdv in collegeAdv.equipes.all():
                if equipe.division == equipeAdv.division:
                    distance = sqrt(int((collegeRef.locationX - collegeAdv.locationX)) ** 2 + (
                            collegeRef.locationY - collegeAdv.locationY) ** 2)
                    if distance > 0:
                        distances.append((equipeAdv, distance))

        # print(distances)
        return distances



    """
    matchupColleges
    Description : Crée les matchups des colleges pour ensuite les remplir avec des équipes.
    Arguments : Aucun
    Retour : 
    """

    def creationMatchs(division):

        def doesMatchNotExist(equipe1, equipe2):
            if (equipe1, equipe2) in matchs or (equipe2, equipe1) in matchs:
                return False
            else:
                return True

        def isTeamNotVisitingCollege(equipeVis, collegeRec, division):
            for match in Match.objects.filter(division=division).all():
                if match.equipe2 == equipeVis and match.equipe1.college == collegeRec:
                    return False

            return True


        matchs = []
        nb_equipes = len(Equipe.objects.filter(division=division).all())
        for equipe in Equipe.objects.all():
            if equipe.division == division:
                equipe.nb_matchVis = 0
                equipe.nb_matchHost = 0
                equipe.save()

        for eIndex in range(nb_equipes):
            equipe = Equipe.objects.filter(division=division).all()[eIndex]

            print(f"-------------{equipe.nom_equipe}----------------")
            # print(equipe, "H" + str(equipe.nb_matchHost), "V" + str(equipe.nb_matchVis))
            for i in range(2):
                if equipe.nb_matchVis + equipe.nb_matchHost < 8:
                    college = equipe.college
                    distances = sorted(calculateDistance(equipe), key=lambda distance: distance[1])
                    index = 0 + i
                    # Les matchs receveurs
                    for equipeAdv, distance in distances:
                        print(equipe, equipeAdv)
                        print(equipe, "H" + str(equipe.nb_matchHost), "V" + str(equipe.nb_matchVis))
                        print(equipeAdv, "H" + str(equipeAdv.nb_matchHost), "V" + str(equipeAdv.nb_matchVis))
                        if doesMatchNotExist(equipe,equipeAdv):
                            print(matchs)
                            print((equipe, equipeAdv))
                            if index % 2 == 0 and equipe.nb_matchHost < 4 and equipeAdv.nb_matchVis < 4 and equipeAdv.nb_matchVis + equipeAdv.nb_matchHost < 8 and isTeamNotVisitingCollege(equipeAdv,equipe.college,equipe.division):
                                match = Match.createMatch(
                                    session=None,
                                    serie=None,
                                    equipe1=equipe,
                                    equipe2=equipeAdv,
                                    semaine=None,
                                    division=division
                                )
                                print("MATCH CREATED : ", (equipe, equipeAdv))
                                matchs.append((equipe, equipeAdv))
                                matchs.append((equipeAdv, equipe))

                            # Les matchs visiteurs
                            elif index % 2 != 0 and equipe.nb_matchVis < 4 and equipeAdv.nb_matchHost < 4 and equipeAdv.nb_matchVis + equipeAdv.nb_matchHost < 8 and isTeamNotVisitingCollege(equipe,equipeAdv.college,equipe.division):
                                match = Match.createMatch(
                                    session=None,
                                    serie=None,
                                    equipe1=equipeAdv,
                                    equipe2=equipe,
                                    semaine=None,
                                    division=division
                                )
                                print("MATCH CREATED : ", (equipeAdv, equipe))
                                matchs.append((equipe, equipeAdv))
                                matchs.append((equipeAdv, equipe))

                        else:
                            print("MATCH ALREADY EXISTS", (equipeAdv, equipe))
                        index += 1

        for match in Match.objects.filter(division=division).all():
            print(match)

        for equipe in Equipe.objects.filter(division=division).all():
            print(equipe.nom_equipe, equipe.nb_matchHost, equipe.nb_matchVis)

        # Correction
        if len(Match.objects.filter(division=division).all()) != nb_equipes * 4:
            nbMatchACorriger = nb_equipes * 4 - len(Match.objects.filter(division=division).all())
            print("NbMatchCorriger : ", nbMatchACorriger)
            for i in range(int(nbMatchACorriger)):
                print("CORRECTION")
                breaked = False
                for equipe in Equipe.objects.filter(division=division).all():

                    # On trouve l'équipe qui lui manque des matchs
                    print(equipe.nom_equipe, equipe.nb_matchHost, equipe.nb_matchVis)
                    if equipe.nb_matchHost + equipe.nb_matchVis < 8:

                        # CAS #1 une équipe manque un match Visiteur et un match Host
                        # Si une équipe manque un match visiteur et un match receveur, il faut simplement delete
                        # un match qui existe deja et reformer deux match avec l'équipe choisi.

                        if equipe.nb_matchHost < 4 and equipe.nb_matchVis < 4:
                            for match in Match.objects.filter(division=division).all():
                                # On check pour un match qui possède des équipes qui n'ont pas de match avec l'équipe choisie
                                if (doesMatchNotExist(equipe, match.equipe1) and doesMatchNotExist(match.equipe2,equipe)
                                        and isTeamNotVisitingCollege(equipe,match.equipe1.college,division)
                                        and isTeamNotVisitingCollege(match.equipe2,equipe.college,division)
                                ):
                                    # On supprime le match et on en créée deux autres
                                    print("NEWMATCH #1 : ", match.equipe1, " VS ", equipe)
                                    match1 = Match.createMatch(
                                        session=None,
                                        serie=None,
                                        equipe1=match.equipe1,
                                        equipe2=equipe,
                                        semaine=None,
                                        division=division
                                    )
                                    print("NEWMATCH #1 : ", equipe, " VS ", match.equipe2)
                                    match2 = Match.createMatch(
                                        session=None,
                                        serie=None,
                                        equipe1=equipe,
                                        equipe2=match.equipe2,
                                        semaine=None,
                                        division=division
                                    )
                                    print("MatchDeleted : ", match.equipe1, " VS ", match.equipe2)
                                    matchDeleted = Match.deleteMatch(match.match_id)
                                    matchs.append((match.equipe1, equipe))
                                    matchs.append((equipe, match.equipe1))

                                    matchs.append((match.equipe2, equipe))
                                    matchs.append((equipe, match.equipe2))

                                    matchs.remove((match.equipe1, match.equipe2))
                                    matchs.remove((match.equipe2, match.equipe1))
                                    breaked = True
                                    break

                            break


                        # CAS #2 : Une équipe manque juste un match Visiteur
                        # Si une équipe manque seulement un match visiteur, il existera une autre équipe qui manquera
                        # un match receveur. Si un match existe deja entre ces deux équipes alors, il faut delete
                        # un match qui existe deja et reformer deux nouveaux matchs.

                        elif equipe.nb_matchHost == 4 and equipe.nb_matchVis < 4:
                            for equipeHost in Equipe.objects.filter(division=division).all():
                                if equipeHost.nb_matchHost < 4 and equipeHost is not equipe:
                                    for match in Match.objects.filter(division=division).all():
                                        if (doesMatchNotExist(equipe, match.equipe1)
                                                and doesMatchNotExist(equipe, match.equipe2)
                                                and doesMatchNotExist(equipeHost, match.equipe1)
                                                and doesMatchNotExist(match.equipe2, equipeHost)
                                                and isTeamNotVisitingCollege(match.equipe2,equipeHost.college, division)
                                        ):
                                            # On delete le match et on en créée deux autres
                                            print("NEWMATCH #1 : ", equipeHost, " VS ", match.equipe2)
                                            match1 = Match.createMatch(
                                                session=None,
                                                serie=None,
                                                equipe1=equipeHost,
                                                equipe2=match.equipe2,
                                                semaine=None,
                                                division=division
                                            )
                                            print("NEWMATCH #1 : ", match.equipe1, " VS ", equipe)
                                            match2 = Match.createMatch(
                                                session=None,
                                                serie=None,
                                                equipe1=match.equipe1,
                                                equipe2=equipe,
                                                semaine=None,
                                                division=division
                                            )
                                            print("MatchDeleted : ", match.equipe1, " VS ", match.equipe2)
                                            matchDeleted = Match.deleteMatch(match.match_id)
                                            matchs.append((equipeHost, match.equipe2))
                                            matchs.append((match.equipe2, equipeHost))

                                            matchs.append((match.equipe1, equipe))
                                            matchs.append((equipe, match.equipe1))

                                            matchs.remove((match.equipe1,match.equipe2))
                                            matchs.remove((match.equipe2, match.equipe1))
                                            breaked = True
                                            break
                                break
                            if breaked:
                                break




                        # CAS #3 : Une équipe manque juste un match Receveur
                        # Si une équipe manque seulement un match receveur, il existera une autre équipe qui manquera
                        # un match visiteur. Si un match existe deja entre ces deux équipes alors, il faut delete
                        # un match qui existe deja et reformer deux nouveaux matchs.

                        elif equipe.nb_matchHost < 4 and equipe.nb_matchVis == 4:
                            for equipeVis in Equipe.objects.filter(division=division).all():
                                if equipeVis.nb_matchVis < 4 and equipeVis is not equipe:
                                    for match in Match.objects.filter(division=division).all():
                                        if (doesMatchNotExist(equipe, match.equipe1)
                                                and doesMatchNotExist(equipe, match.equipe2)
                                                and doesMatchNotExist(equipeVis, match.equipe1)
                                                and doesMatchNotExist(match.equipe2, equipeVis)
                                                and isTeamNotVisitingCollege(equipeVis,match.equipe1.college,division)
                                                and isTeamNotVisitingCollege(match.equipe2,equipe.college,division)
                                        ):
                                            print("NEWMATCH #1 : ", match.equipe1, " VS ", equipeVis)
                                            # On delete le match et on en créée deux autres
                                            match1 = Match.createMatch(
                                                session=None,
                                                serie=None,
                                                equipe1=match.equipe1,
                                                equipe2=equipeVis,
                                                semaine=None,
                                                division=division
                                            )
                                            print("NEWMATCH #2 : ", equipe, " VS ", match.equipe2)
                                            match2 = Match.createMatch(
                                                session=None,
                                                serie=None,
                                                equipe1=equipe,
                                                equipe2=match.equipe2,
                                                semaine=None,
                                                division=division
                                            )
                                            print("MatchDeleted : ", match.equipe1, " VS ", match.equipe2)
                                            matchDeleted = Match.deleteMatch(match.match_id)
                                            matchs.append((equipeVis, match.equipe1))
                                            matchs.append((match.equipe1, equipeVis))

                                            matchs.append((match.equipe2, equipe))
                                            matchs.append((equipe, match.equipe2))

                                            matchs.remove((match.equipe1,match.equipe2))
                                            matchs.remove((match.equipe2, match.equipe1))
                                            breaked = True
                                            break
                                    break
                            if breaked:
                                break

                continue

        for match in Match.objects.filter(division=division).all():
            print(match)

        for equipe in Equipe.objects.filter(division=division).all():
            print(equipe.nom_equipe, equipe.nb_matchHost, equipe.nb_matchVis)


    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def creationCalendrier():
        # Creation d'un calendrier temporaire
        calendrier = Calendrier.createCalendrier(
            annee="2024",
            version="1",
            nbSemaineAut=10,
            nbSemaineHiv=10,
            dateDepartAut="2024-10-02",
            dateDepartHiv="2025-01-22"
        )
        """
            BYPASS_1 : Bypass pour check si le collège ne reçoit pas de matchs cette semaine
            BYPASS_2 : Bypass pour check que les deux équipes ne joue pas cette semaine
            BYPASS_3 : Bypass pour check que les équipes n'ont pas plus de 4 matchs dans la session
            BYPASS_4 : Bypass pour check que l'équipe Receveuse n'a pas plus que 2 matchs receveurs et meme chose Vis
            BYPASS_5 : Bypass pour check que les équipes n'ont pas des matchs dans les 2 dernières semaines
            BYPASS_6 : Bypass pour check que les équipes n'ont pas deux matchs de suites
            BYPASS_7 : Bypass pour
            BYPASS_8 : Bypass
            BYPASS_9 : Bypass

        """
        lastSemaineDate = "2025-03-26"
        def ajoutMatchs(matchs, BYPASS_1, BYPASS_2, BYPASS_3, BYPASS_4, BYPASS_5, BYPASS_6,BYPASS_7,BYPASS_8,BYPASS_9):
            for session in Session.objects.filter(calendrier_id=calendrier.calendrier_id):
                print("NBSEMAINES", session.nb_semaine)
                for semaine in Semaine.objects.filter(session=session).all():
                    print("---- NOUVELLE SEMAINE ----")
                    for match in matchs:
                        # print(match)
                        if match.semaine is None:
                            equipeRec = match.equipe1
                            equipeVis = match.equipe2
                            collegeRec = equipeRec.college
                            print("EQUIPE_REC : ", equipeRec)
                            print("EQUIPE_VIS : ", equipeVis)

                            # Premièrement, on check si le collège ne reçoit pas de matchs cette semaine

                            # Ensuite, on vérifie que les deux équipes ne joue pas cette semaine

                            # Ensuite, on vérifie que les équipes n'ont pas plus de 4 matchs dans la session

                            # Ensuite, on Vérifie que l'équipe Receveuse n'a pas plus que 2 matchs receveurs
                            # dans la session et que l'équipe visiteur n'a pas plus que 2 matchs visiteur dans la session

                            # Finalement, on vérifie que les équipes n'ont pas des matchs dans les 2 dernières semaines
                            if isNotCollegeReceveur(semaine, collegeRec, BYPASS_1) \
                                    and areEquipeLibre(semaine, equipeRec, equipeVis, BYPASS_2) \
                                    and isNotMaxMatchSession(session, equipeRec, equipeVis, BYPASS_3) \
                                    and isNotMaxTypeMatch(session, equipeRec, "R", BYPASS_4) \
                                    and isNotMaxTypeMatch(session, equipeRec, "V", BYPASS_4) \
                                    and isNotThreeMatchStreak(semaine, equipeRec, equipeVis, BYPASS_5) \
                                    and isNotTwoMatchStreak(semaine, equipeRec, equipeVis, BYPASS_6)\
                                    and cegepIsAvailable(collegeRec, semaine,BYPASS_7)\
                                    and equipeIsAvailable(equipeRec,semaine,BYPASS_8)\
                                    and equipeIsAvailable(equipeVis,semaine,BYPASS_8)\
                                    and isNotTangException(equipeVis,semaine,lastSemaineDate,BYPASS_9) \
                                    and isNotTangException(equipeRec, semaine, lastSemaineDate, BYPASS_9):
                                # Si toutes les conditions sont respectés, on ajoute le match à la semaine
                                print('ADDMATCH')
                                match.semaine = semaine
                                match.session = session
                                match.save()

        # On ajoute les matchs en premier lieu
        ajoutMatchs(Match.objects.filter().order_by("?").all(),
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False
                    )

        # CORRECTION
        ajoutMatchs(Match.objects.filter(semaine=None).all(),
                    False,
                    False,
                    True,
                    False,
                    True,
                    True,
                    False,
                    False,
                    False)

        # Correction
        print("CORRECTION FINALE")

        for match in Match.objects.filter(semaine=None).all():
            collegeRec = match.equipe1.college
            equipeRec = match.equipe1
            equipeVis = match.equipe2
            print(match, " : ", collegeRec)

            # Premièrement, on doit trouver une semaine libre qui peut recevoir un match du college receveur
            for session in Session.objects.filter(calendrier_id=calendrier.calendrier_id):
                for semaine in Semaine.objects.filter(session_id=session.session_id):
                    if isNotCollegeReceveur(semaine, collegeRec, False):
                        # Ensuite, on cherche un match déja placé qui pourrait switch
                        for matchToSwitch in Match.objects.filter().all():
                            if matchToSwitch.semaine is not None:
                                if (matchToSwitch.equipe1.division != match.equipe2.division
                                        and areEquipeLibre(semaine, matchToSwitch.equipe1, matchToSwitch.equipe2, False)
                                        and areEquipeLibre(matchToSwitch.semaine, match.equipe1, match.equipe2, False)
                                        and matchToSwitch.equipe1.college == collegeRec
                                        and cegepIsAvailable(collegeRec, semaine, False)
                                        and equipeIsAvailable(equipeRec, semaine, False)
                                        and equipeIsAvailable(equipeVis, semaine, False)
                                        and cegepIsAvailable(match.equipe1.college, matchToSwitch.semaine,False)
                                        and equipeIsAvailable(match.equipe1,matchToSwitch.semaine,False)
                                        and equipeIsAvailable(match.equipe2,matchToSwitch.semaine,False)
                                        and isNotTangException(equipeVis,semaine,lastSemaineDate,False)
                                        and isNotTangException(equipeRec, semaine, lastSemaineDate, False)

                                ):
                                    print("SWITCHED WITH " + str(matchToSwitch))
                                    semaineToSwitch = matchToSwitch.semaine
                                    sessionToSwitch = matchToSwitch.session
                                    match.semaine = semaineToSwitch
                                    match.session = sessionToSwitch
                                    matchToSwitch.semaine = semaine
                                    matchToSwitch.session = session
                                    match.save()
                                    matchToSwitch.save()
                                    break

                        break




        return calendrier

    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def isNotCollegeReceveur(semaine, college, BYPASS_1):

        if BYPASS_1 == True:
            return True

        # for match in Match.objects.filter(semaine=semaine).all():

        collegeReceveurs = [match.equipe1.college for match in Match.objects.filter(semaine=semaine).all()]
        # print(college)
        # print("COLLEGESREC ",collegeReceveurs)
        if college in collegeReceveurs:
            # print('COLLEGE RECOIT DEJA')
            return False
        else:
            # print('COLLEGE LIBRE')
            return True

    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def areEquipeLibre(semaine, teamRec, teamVis, BYPASS_2):

        if BYPASS_2 == True:
            return True

        equipes = []
        for match in Match.objects.filter(semaine=semaine).all():
            equipes.append(match.equipe1)
            equipes.append(match.equipe2)

        if teamRec in equipes or teamVis in equipes:
            return False
        else:
            return True

    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def isNotMaxMatchSession(session, equipeRec, equipeVis, BYPASS_3):

        if BYPASS_3 == True:
            return True

        equipes = []
        for match in Match.objects.filter(session=session).all():
            equipes.append(match.equipe1)
            equipes.append(match.equipe2)

        nbMatchEquipeRec = equipes.count(equipeRec)
        nbMatchEquipeVis = equipes.count(equipeVis)

        # print("MatchEquipeRec : ", nbMatchEquipeRec)
        # print("MatchEquipeVis : ", nbMatchEquipeVis)

        if nbMatchEquipeRec < 4 and nbMatchEquipeVis < 4:
            return True
        else:
            return False

    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """





    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def isNotMaxTypeMatch(session, equipe, type, BYPASS_4):

        if BYPASS_4 == True:
            return True

        equipesRec = []
        equipesVis = []
        nbTypeMatch = 0
        for match in Match.objects.filter(session=session).all():
            print(match)
            equipesRec.append(match.equipe1)
            equipesVis.append(match.equipe2)
        if type == "V":
            nbTypeMatch = equipesVis.count(equipe)

        elif type == "R":
            nbTypeMatch = equipesRec.count(equipe)

        if nbTypeMatch <= 2:
            return True
        else:
            return False

    """
    creationCalendrier
    description : 
    Arguments :
    Retour

    """

    def isNotThreeMatchStreak(semaine, equipeRec, equipeVis, BYPASS_5):

        if BYPASS_5 == True:
            return True

        equipesSemainePrec = []
        try:
            semaine1 = Semaine.objects.get(semaine_id=semaine.semaine_id - 1)
        except Exception as e:
            semaine1 = None
            print(e)

        try:
            semaine2 = Semaine.objects.get(semaine_id=semaine.semaine_id - 2)
        except Exception as e:
            semaine2 = None
            print(e)

        if semaine1 is not None:
            for match in Match.objects.filter(semaine=semaine1).all():
                equipesSemainePrec.append(match.equipe1)
                equipesSemainePrec.append(match.equipe2)

        if semaine2 is not None:
            for match in Match.objects.filter(semaine=semaine2).all():
                equipesSemainePrec.append(match.equipe1)
                equipesSemainePrec.append(match.equipe2)

        if equipesSemainePrec.count(equipeRec) == 2 or equipesSemainePrec.count(equipeVis) == 2:
            return False

        else:
            return True

    def isNotTwoMatchStreak(semaine, equipeRec, equipeVis, BYPASS_6):
        if BYPASS_6 == True:
            return True

        equipesSemainePrec = []
        try:
            semaine1 = Semaine.objects.get(semaine_id=semaine.semaine_id - 1)
        except Exception as e:
            semaine1 = None
            print(e)

        if semaine1 is not None:
            for match in Match.objects.filter(semaine=semaine1).all():
                equipesSemainePrec.append(match.equipe1)
                equipesSemainePrec.append(match.equipe2)

        if equipeRec in equipesSemainePrec or equipeVis in equipesSemainePrec:
            return False

        else:
            return True

    def cegepIsAvailable(college : College, semaine : Semaine, BYPASS_7):
        if BYPASS_7 == True:
            return True
        if college.indisponibilites != None:
            indispos = college.indisponibilites.get("dates",[])
            print(indispos)
            semaineDate = semaine.date.strftime("%Y-%m-%d")
            if semaineDate in indispos:
                return False
            else:
                return True
        else :
            return True

    """
    creationCalendrier
    description :
    Arguments :
    Retour

    """

    def equipeIsAvailable(equipe : Equipe, semaine: Semaine,BYPASS_8):
        if BYPASS_8 == True:
            return True

        if equipe.indisponibilites != None:
            indispos = equipe.indisponibilites.get("dates",[])
            print(indispos)
            semaineDate = semaine.date.strftime("%Y-%m-%d")
            if semaineDate in indispos:
                return False
            else:
                return True
        else:
            return True

    def isNotTangException(equipe,semaine, lastSemaineDate, BYPASS_9):

        if BYPASS_9 == True:
            return False
        semaineDate = semaine.date.strftime("%Y-%m-%d")
        if equipe.division == "Tangerine" and semaineDate == lastSemaineDate:
            return False
        else:
            return True

    creationMatchs("Pamplemousse")
    creationMatchs("Tangerine")
    creationMatchs("Clementine")

    input(f"Matchs crées : {len(Match.objects.all())}. Continue ?")

    calendrier = creationCalendrier()
    for session in Session.objects.filter(calendrier=calendrier).all():
        print("SESSION", session)
        for semaine in Semaine.objects.filter(session=session).all():
            print("SEMAINE", semaine)
            for match in Match.objects.filter(semaine=semaine).all():
                print("MATCH", match)

    for match in Match.objects.filter(semaine=None):
        print("MATCH NONE", match)
    print("NB match non placés : ", len(Match.objects.filter(semaine=None)))


def updateMatchDate():
    for match in Match.objects.all():
        dateSemaine = match.semaine.date
        print(dateSemaine,"-",match.date_match)
        match.date_match = dateSemaine
        print(match.date_match)
        match.save()

    for match in Match.objects.all():
        print(match.date_match)

def createMatchTEST():
    equipeTest = Equipe.objects.get(nom_equipe="EQUIPE TEST")
    for equipe in Equipe.objects.all():
        match = Match.createMatch("Pamplemousse",None,None,equipe,equipeTest,None,datetime.today())
        print(match)


def updateUrlMatch():
    for match in Match.objects.all():
        print(match.get_urlMatch())

def updateMatchcache():
    for match in Match.objects.all():
        match.cache = match.improvisations
        match.save()

def updateMatchImpro():
    for match in Match.objects.all():
        if match.cache is not None:
            improvisations = ast.literal_eval(match.cache)[2]
            match.improvisations = improvisations
            match.save()

def getCoachUrlChangeMDP(coachEmail):
    coachToReset = Coach.objects.filter(courriel__iexact=coachEmail).first()
    # print(coachToReset)
    if coachToReset:
        code = str(coachToReset.prenom_coach) + str(coachToReset.nom_coach) + str(coachToReset.coach_id)
        coachCodeHash = hash_code(code)
        domain = "http://localhost:8000" if settings.DEBUG else "https://citrus.liguedespamplemousses.com"
        urlResetPassword = f"https://citrus.liguedespamplemousses.com/Citrus/ResetPassword-{coachCodeHash}"
        print(urlResetPassword)
def getMissingMatch():
    for match in Match.objects.all():
        if(match.session_id == 81 and match.completed_flag == 0):
            print(match.equipe1_id.nom_equipe + " vs. " + match.equipe2_id.nom_equipe)


def clean_and_parse_cache():

    for match in Match.objects.all():

        if match.cache is not None:
            print(match.cache)
            data = ast.literal_eval(match.cache)
            align1 = data[0]
            align2 = data[1]
            improvisations = [
                {'description': data[2][0][0], 'points' : data[2][0][1]},
                {'description': data[2][1][0], 'points': data[2][1][1]},
                {'description': data[2][2][0], 'points': data[2][2][1]},
                {'description': data[2][3][0], 'points': data[2][3][1]},
                {'description': data[2][4][0], 'points': data[2][4][1]},
                {'description': data[2][5][0], 'points': data[2][5][1]},
                {'description': data[2][6][0], 'points': data[2][6][1]},
                {'description': data[2][7][0], 'points': data[2][7][1]},
                {'description': data[2][8][0], 'points': data[2][8][1]},
                {'description': data[2][9][0], 'points': data[2][9][1]},
                {'description': data[2][10][0], 'points': data[2][10][1]},
                {'description': data[2][11][0], 'points': data[2][11][1]},
                {'description': data[2][12][0], 'points': data[2][12][1]},
            ]
            punitions = []
            for punition in data[3]:
                punitionTemp = {
                    'equipe' : punition[0],
                    'titre' : punition[1],
                    'majeure' : punition[2]
                }
                punitions.append(punitionTemp)

            etoiles = []
            scores = {
                'sousTotal' : {'equipe1' : data[5][0][0], 'equipe2' : data[5][0][1]},
                'penalites': {'equipe1': data[5][1][0], 'equipe2': data[5][1][1]},
                'total': {'equipe1': data[5][2][0], 'equipe2': data[5][2][1]}
            }
            signatures = {
                'coach1' : False,
                'coach2' : False
            }

            jsonData = {
                'alignementEquipe1' : align1,
                'alignementEquipe2' : align2,
                'improvisations' : improvisations,
                'punitions' : punitions,
                'etoiles' : etoiles,
                'scores' : scores,
                'signatures' : signatures
            }

        else:
            improvisations = [
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''},
                {'description': '', 'points': ''}
            ]
            punitions = []

            etoiles = []
            scores = {
                'sousTotal': {'equipe1': '0', 'equipe2': '0'},
                'penalites': {'equipe1': '0', 'equipe2': '0'},
                'total': {'equipe1': '0', 'equipe2': '0'}
            }
            signatures = {
                'coach1': False,
                'coach2': False
            }

            jsonData = {
                'alignementEquipe1': [],
                'alignementEquipe2': [],
                'improvisations': improvisations,
                'punitions': punitions,
                'etoiles': etoiles,
                'scores': scores,
                'signatures': signatures
            }

        match.cache = jsonData
        match.save()



def changeImprovisations():
    for match in Match.objects.all():
        # Check if cache is not None and is a string
        if match.cache:
            try:
                # If it's a string, try to fix the single quotes to double quotes
                if isinstance(match.cache, str):
                    # Fix single quotes to double quotes in the string
                    match.cache = re.sub(r"'", r'"', match.cache)

                    # Try loading the fixed JSON string into a dictionary
                    match.cache = json.loads(match.cache)

                # Access and modify the 'improvisations' key within the cache
                improvisations = match.cache.get('improvisations', [])

                # Example: Add a new improvisation to the list
                improvisations.append({'description': 'New improvisation', 'points': ''})

                # Update the cache with the modified improvisations list
                match.cache['improvisations'] = improvisations

                # Save the modified match object
                match.save()

                print(f"Match ID {match} updated successfully with new improvisations.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON for match ID {match}: {e}")
            except Exception as e:
                print(f"Error processing match ID {match}: {e}")
                continue  # Skip this match if there was an error

def getMatchNotConfirmed():
    for match in Match.objects.all():
        if int(match.cache.get("scores").get("total").get("equipe1")) + int(match.cache.get("scores").get("total").get("equipe1")) != 0 and match.completed_flag == False:
            if match.equipe1.nom_equipe != "EQUIPE TEST" and match.equipe2.nom_equipe != "EQUIPE TEST":
                print(match,match.get_urlMatch)


def getMachManquants():

    matchPamps = []
    matchTangs = []
    matchClems = []

    for match in Match.objects.all():
        if match.completed_flag == False:
            if match.equipe1.nom_equipe != "EQUIPE TEST" and match.equipe2.nom_equipe != "EQUIPE TEST":
                if match.division == "Pamplemousse":
                    #matchPamps.append(match)
                    matchPamps.append((match,match.get_urlMatch))
                if match.division == "Tangerine":
                    #matchTangs.append(match)
                    matchTangs.append((match,match.get_urlMatch))
                if match.division == "Clementine":
                    #matchClems.append(match)
                    matchClems.append((match,match.get_urlMatch))


    print("MATCHS PAMPLEMOUSSES")
    for matchManquant in matchPamps:
        print(matchManquant)

    print("MATCHS TANGERINES")
    for matchManquant in matchTangs:
        print(matchManquant)

    print("MATCHS CLÉMENTINES")
    for matchManquant in matchClems:
        print(matchManquant)




if __name__ == "__main__":

    getMachManquants()
    #updateMatchImpro()
    #updateUrlMatch()
    #Saison.createSaison("2024-2025")
    #createURLMatch()
    #fillCalendrier()
    #calendrier = Calendrier.objects.all().first()
    #exportCalendrier(calendrier)
    #sendCoachEmail("felixrobillard@gmail.com",EmailType.RESETPASSWORD)
    #updateMatchDate()
    pass


