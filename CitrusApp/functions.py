import ast
import re
import os
import django
from django.db.models import Q
import hashlib
from django.conf import settings
from datetime import datetime
import json
import xlwings as xw



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CITRUS.settings')
django.setup()

from Helpers.EmailHelper import EmailHelper
from CitrusApp.admin import CoachCreationForm
from CitrusApp.models import Calendrier, Session, Semaine, Match, College, Equipe, Coach, Saison


def hash_code(code: str) -> str:
    # Create a SHA-256 hash object
    hash_object = hashlib.sha256()

    # Encode the string and update the hash object
    hash_object.update(code.encode('utf-8'))

    # Get the hexadecimal representation of the hash
    hash_hex = hash_object.hexdigest()

    return hash_hex

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
                    matchPamps.append(match)
                    #matchPamps.append((match,match.get_urlMatch))
                if match.division == "Tangerine":
                    matchTangs.append(match)
                    #matchTangs.append((match,match.get_urlMatch))
                if match.division == "Clementine":
                    matchClems.append(match)
                    #matchClems.append((match,match.get_urlMatch))



def getMatchTeams(teamName):
    diffTotal = 0
    equipe = Equipe.objects.get(nom_equipe=teamName)
    for match in Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all():
        if equipe == match.equipe1:
            diff = match.score_eq1 - match.score_eq2
        elif equipe == match.equipe2:
            diff = match.score_eq2 - match.score_eq1
        print(f"{match.equipe1} ({match.score_eq1}) VS {match.equipe2} ({match.score_eq2}) --> Diff : {diff}")
        diffTotal += diff
    print(f"Différentiel Total: {diffTotal}")

def ajoutSemaines():
    filepath = r"C:\Users\felix\Downloads\CalendrierPamps.xlsx"
    wb = xw.Book(filepath)
    sheet = wb.sheets[1]

    row = 2
    col = 4
    while sheet.cells(row,4).value:
        semaineID = sheet.cells(row,4).value
        semaine = Semaine.objects.get(semaine_id=semaineID)
        session = semaine.session
        division = sheet.cells(row,7).value
        equipeVisID = sheet.cells(row,5).value
        equipeVis = Equipe.objects.get(id_equipe=equipeVisID)

        equipeHoteID = sheet.cells(row,6).value
        equipeHote = Equipe.objects.get(id_equipe=equipeHoteID)

        Match.createMatch(division,session,None,equipeHote,equipeVis,semaine)
        print(f"LE MATCH : {equipeVis.nom_equipe} VS {equipeHote.nom_equipe}, Semaine {semaine.date} a été créé")
        row+=1

if __name__ == "__main__":
    emailHelper = EmailHelper()
    emailHelper.courrielInvitation("felixrobillardWork@gmail.com")
    #ajoutSemaines()
    #getMatchTeams("Plan B")
    #getMachManquants()
    #updateMatchImpro()
    #updateUrlMatch()
    #Saison.createSaison("2024-2025")
    #createURLMatch()
    #sendCoachEmail("felixrobillard@gmail.com",EmailType.RESETPASSWORD)
    #updateMatchDate()
    pass


