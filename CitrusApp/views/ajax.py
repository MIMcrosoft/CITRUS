import json

from django.contrib.auth.hashers import check_password
from django.http import JsonResponse

from ..models import Coach, Equipe, Alignement, Match, Saison
from Helpers.EmailHelper import EmailHelper

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages

"""
THESE FUNCTIONS DON'T BELONG HERE
TO MOVE TO API
"""

def saveToDB(request):
    if request.method == "POST":

        try:
            # Parse the incoming JSON data
            data = json.loads(request.body)
            matchData = data.get('data',{})
            matchID = data.get('matchID')
            userID = data.get('userID')

            match = Match.objects.get(match_id=matchID)

            print(matchData)
            print("MATCH SAVED")
            match.cache = matchData
            match.save()
            # Respond with a success message
            return JsonResponse({'status': 'success', 'message': 'Data saved successfully!'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def checkPassword(request):
    if request.method == "POST":
        data = json.loads(request.body)
        password = data.get('password')
        teamID = data.get('teamId')
        matchId = data.get('matchId')

        # Retrieve the team from the database
        equipe = Equipe.objects.get(id_equipe=teamID)
        match = Match.objects.get(match_id=matchId)
        saison = match.saison
        alignement = Alignement.objects.get(equipe=equipe, saison=saison)
        coachs = alignement.coachs.all()

        if any(check_password(password, c.password) for c in coachs):
            return JsonResponse({'message': 'Password matched'},status=200)
        else:
            return JsonResponse({'message': 'Password invalid'},status=401)

        return JsonResponse({'message': 'Invalid request'},status=404)

def validateCoach(request):
    if request.method == "POST":
        try:
            emailHelper = EmailHelper()
            data = json.loads(request.body)
            coachID = data.get('coachID')

            # Ensure `Coach.objects.get` does not raise an exception
            coach = Coach.objects.get(coach_id=coachID)

            if coach:
                coach.validated_flag = True
                emailHelper.courrielValidation(coach.courriel)
                coach.save()
                return JsonResponse({'message': 'Coach validated'}, status=200)

        except Coach.DoesNotExist:
            return JsonResponse({'message': 'Coach not found'}, status=404)
        except KeyError:
            return JsonResponse({'message': 'Invalid data'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON'}, status=400)

    # If the request method is not POST
    return JsonResponse({'message': 'Invalid request method'}, status=405)

@login_required
def selectionner_equipe(request):
    if request.method != "POST":
        return redirect('accueil')  # remplace par le nom de ta vue d'accueil

    equipe_id = request.POST.get('equipe_id')
    if not equipe_id:
        messages.error(request, "Tu dois sélectionner une équipe avant de confirmer.")
        return redirect('accueil')

    equipe = get_object_or_404(Equipe, pk=equipe_id)

    saison = Saison.objects.filter(est_active=True).first()
    if saison is None:
        messages.error(request, "Aucune saison active pour le moment. Contacte un administrateur.")
        return redirect('accueil')

    if not equipe.is_active_pour_saison(saison):
        messages.error(request, "Cette équipe n'est pas active pour la saison en cours.")
        return redirect('accueil')

    coach = request.user

    # Récupère ou crée l'alignement de cette équipe pour la saison active
    alignement, _ = Alignement.objects.get_or_create(
        equipe=equipe,
        saison=saison,
        defaults={'division': equipe.division, 'est_active': equipe.est_active},
    )
    alignement.coachs.add(coach)

    # Garde aussi le coach.equipe à jour pour référence rapide
    coach.equipe = equipe
    coach.save()

    messages.success(request, f"Tu es maintenant associé à l'équipe {equipe.nom_equipe} !")
    return redirect('Accueil')
