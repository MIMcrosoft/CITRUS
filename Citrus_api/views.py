from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from CitrusApp.models import Coach,Equipe,Match
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
                pj = 0  # Matches played
                v = 0   # Wins
                d = 0   # Losses
                dp = 0  # Overtime losses
                pen = 0 # Penalties (assuming you plan to calculate this)
                pp = 0  # Points scored
                pc = 0  # Points conceded
                flagProlong = False  # To track overtime

                # Loop through all matches for the team
                for match in Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all():
                    if match.completed_flag:
                        pj += 1
                        improvisations = ast.literal_eval(match.improvisations)

                        if equipe == match.equipe1:
                            for improvisation in improvisations:
                                if improvisation[1] == "both":
                                    pp += 1
                                elif improvisation[1] == "team1":
                                    pp += 1
                                elif improvisation[1] == "team2":
                                    pc += 1

                            if improvisations[-1][1] != "":
                                flagProlong = True

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
                            for improvisation in improvisations:
                                if improvisation[1] == "both":
                                    pp += 1
                                elif improvisation[1] == "team2":
                                    pp += 1
                                elif improvisation[1] == "team1":
                                    pc += 1

                            if improvisations[-1][1] != "":
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
                    'point': point
                })

            stats = sorted(
                stats,
                key=lambda x: (x['point'], x['diff'], x['pourc_impro_gagner']),
                reverse=True
            )


            return JsonResponse({'division': division, 'stats': stats}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid division'}, status=400)


