import random
import smtplib
from calendar import Calendar
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from math import sqrt
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CITRUS.settings')
django.setup()

from CitrusApp.admin import CoachCreationForm
from CitrusApp.NOTPUBLIC import GMAIL_KEY
from CitrusApp.models import Calendrier, Session, Semaine, Match, College, Equipe

"""

"""


def sendCoachInvite(coachEmail):
    # Création d'un compte temporaire

    coach = creationCompteCoach("UserTest", "UserTest", coachEmail, "IMPROMOMO8866887")

    # Création du lien vers le changement des infos
    urlSignIn = f"localhost:8000/Citrus/CoachSignIn/{coach.id}"

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'felixrobillardwork@gmail.com'
    receiver_email = coachEmail
    password = GMAIL_KEY

    with open("coachEmailInvite.html", 'r', encoding="utf-8") as file:
        html_body = file.read()

    html_bodyParam = html_body.replace("{urlSignIn}", urlSignIn)

    # Contenu du Email
    subject = 'Invitation à la plateforme CITRUS'

    # Création du message du email
    msg = MIMEMultipart('alternative')
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attacher le body du message à l'email
    msg.attach(MIMEText(html_bodyParam, 'html'))

    # Connexion au serveur SMTP et l'envoi du email.

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        print('Le courriel à été envoyer avec succès')
    except Exception as e:
        print(f"Le courriel n'a pas été envoyé : {e}")
    finally:
        server.quit()


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
                        if (equipe, equipeAdv) not in matchs and (equipeAdv, equipe) not in matchs:
                            if index % 2 == 0 and equipe.nb_matchHost < 4 and equipeAdv.nb_matchVis < 4 and equipeAdv.nb_matchVis + equipeAdv.nb_matchHost < 8:
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
                            elif index % 2 != 0 and equipe.nb_matchVis < 4 and equipeAdv.nb_matchHost < 4 and equipeAdv.nb_matchVis + equipeAdv.nb_matchHost < 8:
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
                                if (equipe, match.equipe1) not in matchs and (equipe, match.equipe2) not in matchs:
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
                                    break


                        # CAS #2 : Une équipe manque juste un match Visiteur
                        # Si une équipe manque seulement un match visiteur, il existera une autre équipe qui manquera
                        # un match receveur. Si un match existe deja entre ces deux équipes alors, il faut delete
                        # un match qui existe deja et reformer deux nouveaux matchs.

                        elif equipe.nb_matchHost == 4 and equipe.nb_matchVis < 4:
                            for equipeHost in Equipe.objects.filter(division=division).all():
                                if equipeHost.nb_matchHost < 4 and equipeHost is not equipe:
                                    for match in Match.objects.filter(division=division).all():
                                        if (equipe, match.equipe1) not in matchs \
                                                and (equipe, match.equipe2) not in matchs \
                                                and (equipeHost, match.equipe1) not in matchs \
                                                and (equipeHost, match.equipe2) not in matchs:
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
                                            break



                        # CAS #3 : Une équipe manque juste un match Receveur
                        # Si une équipe manque seulement un match receveur, il existera une autre équipe qui manquera
                        # un match visiteur. Si un match existe deja entre ces deux équipes alors, il faut delete
                        # un match qui existe deja et reformer deux nouveaux matchs.

                        elif equipe.nb_matchHost < 4 and equipe.nb_matchVis == 4:
                            for equipeVis in Equipe.objects.filter(division=division).all():
                                if equipeVis.nb_matchVis < 4 and equipeVis is not equipe:
                                    for match in Match.objects.filter(division=division).all():
                                        if (equipe, match.equipe1) not in matchs \
                                                and (equipe, match.equipe2) not in matchs \
                                                and (equipeVis, match.equipe1) not in matchs \
                                                and (equipeVis, match.equipe2) not in matchs:
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
        )
        """
            BYPASS_1 : Bypass pour check si le collège ne reçoit pas de matchs cette semaine
            BYPASS_2 : Bypass pour check que les deux équipes ne joue pas cette semaine
            BYPASS_3 : Bypass pour check que les équipes n'ont pas plus de 4 matchs dans la session
            BYPASS_4 : Bypass pour check que l'équipe Receveuse n'a pas plus que 2 matchs receveurs et meme chose Vis
            BYPASS_5 : Bypass pour check que les équipes n'ont pas des matchs dans les 2 dernières semaines
            BYPASS_6 : Bypass pour check que les équipes n'ont pas deux matchs de suites
        
        """
        def ajoutMatchs(matchs, BYPASS_1, BYPASS_2, BYPASS_3, BYPASS_4, BYPASS_5,BYPASS_6):
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
                                    and isNotThreeMatchStreak(semaine, equipeRec, equipeVis, BYPASS_5)\
                                    and isNotTwoMatchStreak(semaine,equipeRec, equipeVis, BYPASS_6):
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
                    False)

        # CORRECTION
        ajoutMatchs(Match.objects.filter(semaine=None).all(),
                    False,
                    False,
                    True,
                    True,
                    True,
                    True)

        #Correction
        print("CORRECTION FINALE")

        for match in Match.objects.filter(semaine=None).all():
            collegeRec = match.equipe1.college
            equipeRec = match.equipe1
            equipeVis = match.equipe2
            print(match," : ",collegeRec)

            #Premièrement, on doit trouver une semaine libre qui peut recevoir un match du college receveur
            for session in Session.objects.filter(calendrier_id=calendrier.calendrier_id):
                for semaine in Semaine.objects.filter(session_id=session.session_id):
                    if isNotCollegeReceveur(semaine,collegeRec,False):
                        #Ensuite, on cherche un match déja placé qui pourrait switch
                        for matchToSwitch in Match.objects.filter().all():
                            if matchToSwitch.semaine is not None:
                                if matchToSwitch.equipe1.division != match.equipe2.division\
                                and areEquipeLibre(semaine,matchToSwitch.equipe1,matchToSwitch.equipe2,False)\
                                and areEquipeLibre(matchToSwitch.semaine,match.equipe1,match.equipe2,False)\
                                and matchToSwitch.equipe1.college == collegeRec:
                                    semaineToSwitch = matchToSwitch.semaine
                                    sessionToSwitch = matchToSwitch.session
                                    match.semaine = semaineToSwitch
                                    match.session = sessionToSwitch
                                    matchToSwitch.semaine = semaine
                                    matchToSwitch.session = session
                                    match.save()
                                    matchToSwitch.save()



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

    def isNotTwoMatchStreak(semaine,equipeRec,equipeVis,BYPASS_6):
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


if __name__ == "__main__":
    fillCalendrier()
