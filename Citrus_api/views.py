from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from CitrusApp.models import Coach,Equipe,Match,Punition
from .serializers import *
import ast
from django.http import JsonResponse

# Create your views here.

DIVISION_CHOICES = [
    ("Pamplemousse", "Pamplemousse"),
    ("Tangerine", "Tangerine"),
    ("Clementine", "Clementine")
]
@api_view(['GET'])
def classement(request, division):
    if request.method == 'GET':
        if (division,division) in DIVISION_CHOICES:
            stats = []  # List to hold stats for all teams
            for equipe in Equipe.objects.filter(division=division):

                if "EQUIPE TEST" in equipe.nom_equipe:
                    continue

                pj = 0  # Matches played
                v = 0   # Wins
                d = 0   # Losses
                dp = 0  # Overtime losses
                pen = 0 # Penalties (assuming you plan to calculate this)
                pp = 0  # Points scored
                pc = 0  # Points conceded
                  # To track overtime

                # Loop through all matches for the team
                for match in Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all():
                    flagProlong = False
                    if "EQUIPE TEST" in match.equipe1.nom_equipe or "EQUIPE TEST" in match.equipe2.nom_equipe:
                        continue

                    if match.completed_flag:
                        pj += 1
                        improvisations = match.improvisations

                        if equipe == match.equipe1:
                            pp += match.score_eq1
                            pc += match.score_eq2


                            if improvisations[12].get("points") != "":
                                flagProlong = True
                            else:
                                flagProlong = False

                            if flagProlong:
                                if match.score_eq1 > match.score_eq2:
                                    v += 1
                                elif match.score_eq1 < match.score_eq2:
                                    dp += 1
                            else:
                                if match.score_eq1 > match.score_eq2:
                                    v += 1
                                elif match.score_eq1 < match.score_eq2:
                                    d += 1

                        elif equipe == match.equipe2:
                            pp += match.score_eq2
                            pc += match.score_eq1

                            if improvisations[12].get("points") != "":
                                flagProlong = True

                            if flagProlong:
                                if match.score_eq2 > match.score_eq1:
                                    v += 1
                                elif match.score_eq2 < match.score_eq1:
                                    dp += 1
                            else:
                                if match.score_eq2 > match.score_eq1:
                                    v += 1
                                elif match.score_eq2 < match.score_eq1:
                                    d += 1

                pen += len(Punition.objects.filter(equipe_punie=equipe))




                # Calculate additional stats
                pourc_impro_gagner = (pp / (pp + pc) * 100) if (pp + pc) > 0 else 0
                diff = pp - pc
                point = 2 * v + dp

                # Append stats for the current team
                stats.append({
                    'equipe': equipe.nom_equipe,  # Assuming Equipe has a name field
                    'pj': pj,
                    'v': v,
                    'd': d,
                    'dp': dp,
                    'pen': pen,
                    'pp': pp,
                    'pc': pc,
                    'pourc_impro_gagner': pourc_impro_gagner,
                    'diff': diff,
                    'point': point,
                    'logo': equipe.getUrlPhoto()
                })

            stats = sorted(
                stats,
                key=lambda x: (x['point'], x['diff'], x['pourc_impro_gagner']),
                reverse=True
            )


            return JsonResponse({'division': division, 'stats': stats}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid division'}, status=400)


