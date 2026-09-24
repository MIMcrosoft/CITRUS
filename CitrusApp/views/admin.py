import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Coach, Equipe, Saison, Match, Alignement, DIVISION_CHOICES

VALID_DIVISIONS = {value for value, _ in DIVISION_CHOICES}


def _require_admin(request):
    current_user = request.user
    return bool(current_user.is_authenticated and current_user.admin_flag)


@login_required
def panneau_admin(request, id_saison=None):
    current_user = request.user
    if not current_user.admin_flag:
        return redirect('/Citrus/Accueil')

    saisons = Saison.objects.all().order_by('-saison_id')

    if id_saison:
        saison_selectionnee = get_object_or_404(Saison, saison_id=id_saison)
    else:
        saison_selectionnee = Saison.objects.filter(est_active=True).first() or saisons.first()

    allUsers = Coach.objects.filter(is_superuser=False).select_related('equipe').order_by('nom_coach')
    nb_coachs_non_valides = allUsers.filter(validated_flag=False).count()

    alignementsActives = Alignement.objects.none()
    if saison_selectionnee:
        alignementsActives = Alignement.objects.filter(saison=saison_selectionnee, est_active=True)
    repartitionEquipes = {
        division: alignementsActives.filter(division=division).count()
        for division, _ in DIVISION_CHOICES
    }

    matchsSaison = Match.objects.none()
    repartitionMatchs = {}
    nbMatchsCompletes = 0
    nbMatchsTotal = 0
    if saison_selectionnee:
        matchsSaison = Match.objects.filter(saison=saison_selectionnee).select_related(
            'equipe1', 'equipe2'
        ).order_by('date_match')
        nbMatchsTotal = matchsSaison.count()
        nbMatchsCompletes = matchsSaison.filter(completed_flag=True).count()
        repartitionMatchs = {
            division: matchsSaison.filter(division=division).count()
            for division, _ in DIVISION_CHOICES
        }

    return render(request, "panneau_admin.html", {
        'activeTab': "ADMIN",
        'saisons': saisons,
        'saison_selectionnee': saison_selectionnee,
        'allUsers': allUsers,
        'matchs': matchsSaison,
        'dashboard': {
            'nb_equipes': alignementsActives.count(),
            'repartition_equipes': repartitionEquipes,
            'nb_coachs': allUsers.count(),
            'nb_coachs_non_valides': nb_coachs_non_valides,
            'nb_saisons': saisons.count(),
            'nb_matchs_total': nbMatchsTotal,
            'nb_matchs_completes': nbMatchsCompletes,
            'nb_matchs_a_venir': nbMatchsTotal - nbMatchsCompletes,
            'repartition_matchs': repartitionMatchs,
        },
    })

@login_required
def ajouter_saison(request):
    if not _require_admin(request):
        return JsonResponse({'message': 'Accès refusé'}, status=403)

    if request.method != "POST":
        return JsonResponse({'message': 'Méthode invalide'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'JSON invalide'}, status=400)

    nom_saison = (data.get('nom_saison') or '').strip()
    if not nom_saison:
        return JsonResponse({'message': "Le nom de la saison est requis"}, status=400)

    saison = Saison.createSaison(nom_saison)

    return JsonResponse({
        'message': 'Saison créée',
        'saison_id': saison.saison_id,
        'nom_saison': saison.nom_saison,
    }, status=201)

@login_required
def activer_saison(request, id_saison):
    if not _require_admin(request):
        return JsonResponse({'message': 'Accès refusé'}, status=403)

    if request.method != "POST":
        return JsonResponse({'message': 'Méthode invalide'}, status=405)

    saison = get_object_or_404(Saison, saison_id=id_saison)
    saison.set_active()

    return JsonResponse({'message': 'Saison activée', 'saison_id': saison.saison_id})

@login_required
def modifier_alignement_saison(request):
    if not _require_admin(request):
        return JsonResponse({'message': 'Accès refusé'}, status=403)

    if request.method != "POST":
        return JsonResponse({'message': 'Méthode invalide'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'JSON invalide'}, status=400)

    equipe = get_object_or_404(Equipe, pk=data.get('equipe_id'))
    saison = get_object_or_404(Saison, saison_id=data.get('saison_id'))

    division = data.get('division')
    if division and division not in VALID_DIVISIONS:
        return JsonResponse({'message': 'Division invalide'}, status=400)

    alignement, _ = Alignement.objects.get_or_create(
        equipe=equipe,
        saison=saison,
        defaults={'division': equipe.division, 'est_active': equipe.est_active},
    )

    if division:
        alignement.division = division
    if 'est_active' in data:
        alignement.est_active = bool(data.get('est_active'))
    alignement.save()

    return JsonResponse({
        'message': 'Alignement mis à jour',
        'equipe_id': equipe.id_equipe,
        'saison_id': saison.saison_id,
        'division': alignement.division,
        'est_active': alignement.est_active,
    })
