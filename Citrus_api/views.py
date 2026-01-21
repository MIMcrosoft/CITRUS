from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from CitrusApp.models import Coach, Equipe, Match, Punition, Interprete, Alignement, DetailsInterprete, Saison, RequeteReportMatch
from Helpers.EmailHelper import EmailHelper
from .serializers import *
import ast
from datetime import datetime
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
            saison = Saison.objects.get(est_active=True)
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
                for match in Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all():
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
                    for punition in match.punitions.all():
                        if punition.equipe_punie == equipe:
                            pen += 1

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
                key=lambda x: (x['point'], x['v'], x['diff'], x['pourc_impro_gagner'], x['pp'], -x['pen']),
                reverse=True
            )


            return JsonResponse({'division': division, 'stats': stats}, safe=False)
        else:
            return JsonResponse({'error': 'Invalid division'}, status=400)

@api_view(['GET'])
def get_pronoms_interprete(request, interprete_id):
    interprete = Interprete.objects.filter(interprete_id=interprete_id).first()
    return JsonResponse({
        "pronoms" : interprete.pronom_interprete,
        "nom" : interprete.nom_interprete,
    })

@api_view(['POST'])
def creer_interprete(request):

    alignement = Alignement.objects.filter(id_alignement=request.POST['alignement_id']).first()

    Interprete.createInterprete(
        nom_interprete=request.POST['nom_interprete'],
        pronom_interprete=request.POST['pronom_interprete'],
        numero_interprete=request.POST['numero_interprete'],
        role_interprete=request.POST['role_interprete'],
        alignement=alignement
    )

    return JsonResponse({
        "success": True
    })

@api_view(['POST'])
def ajouter_interprete_alignement(request):

    alignement = Alignement.objects.filter(id_alignement=request.POST['alignement_id']).first()
    interprete = Interprete.objects.filter(interprete_id=request.POST['interprete_id']).first()

    alignement.ajouter_interprete(
        interprete=interprete,
        role_interprete=request.POST['role_interprete'],
        numero_interprete=request.POST['numero_interprete']
    )

    return JsonResponse({
        "success": True
    })

@api_view(['POST'])
def modifier_interprete(request):
    alignement = Alignement.objects.filter(id_alignement=request.POST['alignement_id']).first()
    interprete = Interprete.objects.filter(interprete_id=request.POST['interprete_id']).first()
    detailsInterprete = DetailsInterprete.objects.filter(interprete_id=request.POST['interprete_id'], alignement=alignement).first()

    interprete.pronom_interprete = request.POST['pronom_interprete']
    detailsInterprete.numero_interprete = request.POST['numero_interprete']
    detailsInterprete.role_interprete = request.POST['role_interprete']

    interprete.save()
    detailsInterprete.save()

    return JsonResponse({
        "success": True
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def creer_requete_report_match(request):
    current_user = request.user
    match_id = request.data.get('match_id')
    nouvelle_date = request.data.get('nouvelle_date')


    if not match_id or not nouvelle_date:
        return Response({"error": "match et nouvelle_date sont requis"}, status=400)

    # Vérifier match
    match = Match.objects.filter(match_id=match_id).first()
    if not match:
        return Response({"error": "Match introuvable"}, status=404)

    try:
        nouvelle_date_obj = datetime.fromisoformat(nouvelle_date)
    except:
        return Response({"error": "Format de date invalide (ISO attendu)"}, status=400)

    alignementEq1 = Alignement.objects.get(equipe=match.equipe1, saison=match.saison)
    coachEq1 = alignementEq1.coach

    alignementEq2 = Alignement.objects.get(equipe=match.equipe2, saison=match.saison)
    coachEq2 = alignementEq2.coach


    # Créer la demande
    rr = RequeteReportMatch.objects.create(
        match=match,
        nouvelle_date=nouvelle_date_obj,
        cree_par=request.user,
        coach_1=coachEq1,
        coach_2=coachEq2,
    )

    if coachEq1 is not None and current_user.coach_id == coachEq1.coach_id:
        rr.coach1_validation = True
    elif coachEq2 is not None and current_user.coach_id == coachEq2.coach_id:
        rr.coach2_validation = True

    rr.save()
    # Envoi des courriels
    emailHelper = EmailHelper()
    emailHelper.courrielCreationReportMatch(
        coachEq1.courriel if coachEq1 else None,
        coachEq2.courriel if coachEq2 else None,
        EmailHelper.COURRIEL_ADMIN,
        rr)

    return Response({
        "success": True,
        "message": "Demande de report créée et courriels envoyés.",
        "token": str(rr.token)
    }, status=201)




