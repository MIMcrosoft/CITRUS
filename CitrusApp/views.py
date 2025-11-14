from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from Helpers.EmailHelper import EmailHelper
from .models import Coach, Equipe, College, Interprete, Saison, Alignement, Match, CoachManager, Punition, \
    DetailsInterprete
from .functions import *
import json
from django.http import JsonResponse
from django.contrib.auth.hashers import check_password

def composants_html(request):
    return render(request, 'composants_individuels.html')

def test(request):
    return render(request, 'templatesCourriel/email_code_QR.html')

def page_404(request,exception):
    return render(request, 'fenetre_erreur.html', {
        'errorMsg': "Oups Cette page n'existe pas !"
    })

def accueil(request):
    current_user = request.user

    if isinstance(current_user, AnonymousUser) or not current_user.is_authenticated:
        # Redirect or handle the case when the user is not logged in
        return redirect('Connexion')

    if current_user.is_superuser == True:
        allMatchs = Match.objects.all()
    else:
        equipe = current_user.information_equipe
        allMatchs = Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all()
    if request.method == 'POST':
        pass

    return render(request, 'accueil.html', {"user": current_user,
                                            'allMatchs': allMatchs,
                                            'activeTab' : "ACCUEIL"
                                            })

@login_required
def gestion_utilisateurs(request):
    current_user = request.user
    if request.method == 'POST':
        pass

    if settings.DEBUG:
        domain = "http://localhost:8000"
    else:
        domain = "https://citrus.liguedespamplemousses.com"

    if current_user.admin_flag == True:

        return render(request, "admin_gestion_utilisateurs.html", {
            'allUsers' : Coach.objects.all(),
            'domain' : domain,
            'activeTab': "USER"
        })

    else:
        return redirect("UserPage",current_user.coach_id)

@login_required
def profile_utilisateur(request, userID):
    current_user = request.user
    if settings.DEBUG:
        domain = "http://localhost:8000"
    else:
        domain = "https://citrus.liguedespamplemousses.com"
    if request.method == 'POST':
        pass

    return render(request, "profil_utilisateur.html", {
        'user' : Coach.objects.get(coach_id=userID),
        'domain' : domain,
        'activeTab': "USER"
    })

def reinitialisation_mdp(request, hashedCoachID):
    errors = []
    coachIDToReset = -1
    coachToReset = None
    for coach in Coach.objects.all():
        code = str(coach.prenom_coach)+str(coach.nom_coach)+str(coach.coach_id)

        if hashedCoachID == hash_code(code):
            coachIDToReset = coach.coach_id
            pass
    if coachIDToReset != -1:
        coachToReset = Coach.objects.get(coach_id=coachIDToReset)


    if request.method == "POST":
        if coachToReset is not None:
            newPassword = request.POST['newPassword']
            newPassword2 = request.POST['newPassword2']

            if newPassword != newPassword2:
                errors.append('Les mots de passe sont différents.')
                return render(request, "reinitialisation_mdp.html", {
                    'errors': errors,
                    'allEquipes': Equipe.objects.all()
                })
            elif len(newPassword) < 8 :
                errors.append('Le nouveau mot de passe est trop court.')
                return render(request, "reinitialisation_mdp.html", {
                    'errors': errors,
                    'allEquipes': Equipe.objects.all()
                })

            else:
                coachToReset.set_password(newPassword)
                coachToReset.save()
                return redirect("Connexion")

    return render(request, "reinitialisation_mdp.html", {
        'errors' : errors,
    })

def connexion_utilisateur(request):
    errors = []
    if request.method == 'POST':

        buttonClicked = request.POST.get('button')

        if buttonClicked == 'connexion':

            username = request.POST['username'].strip().lower()
            password = request.POST['password']
            try:
                user = Coach.objects.get(courriel=username)
                # User exists, so authenticate with the password
                authenticated_user = authenticate(request, username=username, password=password)
                if authenticated_user is not None:
                    if authenticated_user.validated_flag:
                        login(request, authenticated_user)
                        return redirect('/Citrus/?animation=2')  # Redirect to home on successful login
                    else:
                        errors.append("Votre compte est en attente de validation par l'administration.")
                else:
                    errors.append("Le mot de passe est incorrect.")
            except Coach.DoesNotExist:
                errors.append("Aucun compte n'est associé à ce nom d'utilisateur.")


        elif buttonClicked == 'resetPassword':
            emailHelper = EmailHelper()
            email = request.POST['emailToReset'].strip().lower()
            coachToReset = Coach.objects.filter(courriel__iexact=email).first()
            #print(coachToReset)
            if coachToReset:
                code = str(coachToReset.prenom_coach) + str(coachToReset.nom_coach) + str(coachToReset.coach_id)
                emailHelper.courrielResetPwd(coachToReset)
                print("COURRIEL ENVOYÉ")

            return redirect('Connexion')

        elif buttonClicked == "inscription":
            pass

    return render(request, "connexion_utilisateur.html", {
        'errors' : errors
    })

def inscription_coach(request):
    errors = []
    if request.method == 'POST':
        coachPrenom = request.POST.get('coachPrenom')
        coachNom = request.POST['coachNom']
        coachPronom = request.POST.get('coachPronom')
        coachCourriel = request.POST['coachCourriel']
        coachPassword = request.POST['coachPassword']
        coachPassword2 = request.POST['coachPassword2']
        coachTeamId = request.POST.get('teamCoach')  # Assuming this is the team ID from the form

        # Check if passwords match
        if coachPassword != coachPassword2:
            errors.append('Les mots de passe sont différents.')
            return render(request, "inscription_coach.html", {
                'errors': errors,
                'allEquipes': Equipe.objects.all()
            })

        if Coach.objects.filter(courriel=coachCourriel).exists():
            errors.append('Un utilisateur avec ce courriel existe déja !')
            return render(request, "inscription_coach.html", {
                'errors': errors
            })

        # Retrieve the team from the database
        coachTeam = Equipe.objects.get(id_equipe=coachTeamId)

        # Create the coach using CoachManager
        coach = Coach.objects.create_user(
            prenom_coach=coachPrenom,
            nom_coach=coachNom,
            pronom_coach=coachPronom,
            courriel=coachCourriel.strip().lower(),
            password=coachPassword,
            equipe=coachTeam
        )

        # Optionally redirect to a login or success page after successful signup
        return redirect('Connexion')  # Assuming you have a login view

    # Render the signup form with all available teams
    return render(request, "inscription_coach.html", {
        'allEquipes': Equipe.objects.all(),
        'errors': errors
    })

@login_required
def gestion_equipes(request):
    current_user = request.user
    saisonActive = Saison.objects.get(est_active=True)
    if request.method == 'POST':
        pass
    if current_user.is_superuser == True:
        allEquipes = Equipe.objects.all()
        return render(request, "admin_equipes.html", {
            'allEquipes': allEquipes,
            'saisonActive': saisonActive,
            'activeTab': "EQUIPE"
        })
    else:
        return redirect('Equipe', current_user.information_equipe.id_equipe, 0)

@login_required
def mes_equipes(request):
    current_user = request.user
    alignements = current_user.alignements.all()

    return render(request, "mes_equipes.html", {
        'alignements': alignements,
        'activeTab' : "EQUIPE"
    })

@login_required
def information_equipe(request, id_equipe, id_saison=None):

    equipe = get_object_or_404(Equipe, id_equipe=id_equipe)
    if id_saison:
        saison = get_object_or_404(Saison, saison_id=id_saison)
        alignement = Alignement.objects.filter(equipe=equipe, saison=saison).first()
        details_interpretes = DetailsInterprete.objects.filter(alignement=alignement).select_related("interprete")
        coach = alignement.coach

        # Handle logic where both `equipe` and `saison` are used
    else:
        saison = Saison.objects.get(est_active=True)
        alignement = Alignement.objects.filter(equipe=equipe, saison=saison).first()
        details_interpretes = None
        coach = alignement.coach

    if request.method == 'POST':
        pass

    return render(request, "informations_equipe.html",
                  {'equipe': equipe,
                   'saisons': Saison.objects.all(),
                   'alignement': alignement,
                   'coach': coach,
                   'matchs_saisons' : Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all(),
                   'activeTab': "EQUIPE",
                   'current_user' : request.user,
                   'saison_selectionne' : saison,
                   'interpretes' : Interprete.objects.all().order_by('nom_interprete'),
                   'details_interpretes': details_interpretes,
                   })

@login_required
def modification_equipe(request, idEquipe):
    current_user = request.user
    equipe = get_object_or_404(Equipe, id_equipe=idEquipe)
    alignement = None
    if request.method == 'POST':
        newNomEquipe = request.POST.get('newNomEquipe')
        if newNomEquipe != None:
            newLogoEquipe = request.FILES['logoEquipe']
        # Ajouter un check erreur de Unique
        newCollegeID = request.POST.get('newCollegeEquipe')
        #print(newCollegeID)

        equipe.nom_equipe = newNomEquipe
        equipe.college = College.objects.get(college_id=newCollegeID)
        equipe.logo = newLogoEquipe

        equipe.save()

        return redirect('Equipe', equipe.id_equipe, 0)


    return render(request, "modification_equipe.html", {
        'equipe': equipe,
        'allSaisons': Saison.objects.all(),
        'alignement': alignement,
        'allColleges': College.objects.all(),
        'activeTab': "EQUIPE"
    })

@login_required
def ajout_equipe(request):
    if request.method == 'POST':
        nomEquipe = str(request.POST['nomEquipe'])
        divisionEquipe = str(request.POST['divisionEquipe'])
        logoEquipe = request.FILES['logoEquipe']
        collegeIDEquipe = int(request.POST['collegeEquipe'])
        coachIDEquipe = int(request.POST['coachEquipe'])
        # indispoEquipe

        #print(nomEquipe, divisionEquipe, collegeIDEquipe, coachIDEquipe)
        collegeEquipe = College.objects.get(college_id=collegeIDEquipe)
        coach = Coach.objects.get(coach_id=coachIDEquipe)

        equipe = Equipe.createEquipe(
            nomEquipe=nomEquipe,
            logo=logoEquipe,
            division=divisionEquipe,
            college=collegeEquipe
        )

        coach.information_equipe = equipe
        coach.save()

        return redirect('Equipes')
    current_user = request.user
    allColleges = College.objects.all()
    allCoachs = Coach.objects.all()
    if current_user.is_superuser == True:
        return render(request, "ajout_equipe.html", {
            'allColleges': allColleges,
            'allCoachs': allCoachs,
            'activeTab': "EQUIPE"

        })

@login_required
def ajout_interprete(request,alignementID):

    alignement = Alignement.objects.get(id_alignement=alignementID)
    if request.method == 'POST':

        buttonClicked = request.POST.get('button')

        nomInterprete = request.POST['nomInterprete']
        pronomsInterprete = request.POST['pronomsInterprete']
        numInterprete = request.POST['numInterprete']
        # Role
        roleInterprete = request.POST.get('radioRoleInterprete')

        alignement = Alignement.objects.get(id_alignement=alignementID)

        interprete = Interprete.createInterprete(
            nom_interprete=nomInterprete,
            pronom_interprete=pronomsInterprete,
            numero_interprete=numInterprete,
            role_interprete=roleInterprete,
            alignement=alignement
        )
        interprete.save()

        if buttonClicked == "addAndReturn":
            print("RETURNING")
            return redirect('Equipe',0)

    return render(request, "ajout_interprete_modal.html",
                  {
                      'equipe': alignement.equipe,
                      'alignement': Alignement.objects.get(id_alignement=alignementID),
                      'interpretes': Interprete.objects.all().order_by('nom_interprete'),
                      'modifyFlag': False,
                      'activeTab': "EQUIPE"
                  })

@login_required
def modification_interprete(request, interpreteID, equipeID):
    allInterpretes = Interprete.objects.all()
    if request.method == 'POST':
        newPronomsInterprete = request.POST['pronomsInterprete']
        newNumInterpretes = request.POST['numInterprete']
        newRoleInterprete = request.POST.get('radioRoleInterprete')

        interprete = Interprete.objects.get(interprete_id=interpreteID)
        interprete.pronom_interprete = newPronomsInterprete
        interprete.numero_interprete = newNumInterpretes
        interprete.role_interprete = newRoleInterprete
        interprete.save()

        return redirect('Equipe',equipeID,0)

    return render(request, "ajout_interprete_modal.html", {
        'equipe': Equipe.objects.get(id_equipe=equipeID),
        'interprete' : Interprete.objects.get(interprete_id=interpreteID),
        'allInterpretes': allInterpretes,
        'modifyFlag' : True,
        'activeTab': "EQUIPE"
    })

@login_required()
def mes_matchs(request, id_saison=None):
    current_user = request.user
    if id_saison is None:
        saison = Saison.objects.get(est_active=True)
    else:
        try:
            saison = Saison.objects.get(saison_id=id_saison)
        except Saison.DoesNotExist:
            saison = Saison.objects.get(est_active=True)
            return redirect('MesMatchs',saison.saison_id)
    alignement = Alignement.objects.get(Q(saison=saison) & Q(coach=current_user))
    equipe = alignement.equipe

    return render(request, "mes_matchs.html", {
        'equipe': equipe,
        'saisons' : Saison.objects.all(),
        'saison_selectionne' : saison,
        'matchs' : Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all(),
        'activeTab': "MATCH",
    })

def reporter_match(request):
    return render(request, "formulaire_report_match.html", {
        'activeTab': "MATCH"
    })
def formulaire_match(request, hashedCode):

    matchSelected = None
    TEST = False

    if settings.DEBUG:
        domain = "http://localhost:8000"
    else:
        domain = "https://citrus.liguedespamplemousses.com"

    for match in Match.objects.all():
        code = str(match.equipe1) + str(match.equipe2) + str(match.match_id)

        if hashedCode == hash_code(code):
            #print(code)
            matchSelected = match

    if matchSelected.equipe1.nom_equipe == "EQUIPE TEST" or matchSelected.equipe2.nom_equipe == "EQUIPE TEST":
        TEST = True

    if request.method == 'POST':
        matchData = matchSelected.cache
        matchSelected.score_eq1 = matchData.get('scores').get('total').get('equipe1')
        matchSelected.score_eq2 = matchData.get('scores').get('total').get('equipe2')
        if not TEST:
            matchSelected.completed_flag = True
            matchSelected.improvisations = matchData.get("improvisations")

            for punition in matchData.get("punitions"):
                equipe = Equipe.objects.get(nom_equipe=punition[0])
                if punition[2] == "Oui":
                    est_majeure = True
                else:
                    est_majeure = False

                Punition.createPunition(punition[1],est_majeure,equipe)
        matchSelected.save()
        print("MATCHSAVED")

    if matchSelected is not None:
        saison = Saison.objects.get(est_active=True)
        alignementEquipe1 = Alignement.objects.filter(equipe=matchSelected.equipe1, saison=saison).first()
        detailsInterpretesEq1 = DetailsInterprete.objects.filter(alignement=alignementEquipe1).select_related("interprete")
        coachEquipe1 = alignementEquipe1.coach

        alignementEquipe2 = Alignement.objects.filter(equipe=matchSelected.equipe2, saison=saison).first()
        detailsInterpretesEq2 = DetailsInterprete.objects.filter(alignement=alignementEquipe2).select_related("interprete")
        coachEquipe2 = alignementEquipe2.coach

        # Your original code
        if matchSelected.cache is not None:
            matchData = matchSelected.cache
        else:
            matchData = None

        current_user = request.user

        if isinstance(current_user, AnonymousUser) or not current_user.is_authenticated:
            current_user = None

        return render(request, 'formulaire_match.html', {
            "match" : matchSelected,
            'coachEquipe1' : coachEquipe1,
            'coachEquipe2' : coachEquipe2,
            'equipe1Alignement' : detailsInterpretesEq1,
            'equipe2Alignement' : detailsInterpretesEq2,
            'matchData' : matchData,
            'hashedPwdsCoach1':None,
            'hashedPwdsCoach2':None,
            'domain': domain,
            'current_user': current_user
        })

def fiche_code_QR(request, equipeId, saisonId):

    equipe =Equipe.objects.get(id_equipe=equipeId)
    saison =Saison.objects.get(saison_id=saisonId)

    return render(request, "fiche_code_QR.html", {
        'equipe' : equipe,
        'matchs' : Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all()
    })
@login_required
def calendrierAdmin(request):
    if request.method == 'POST':
        pass

    return render(request, "calendrier/calendrier-step0.html", {
        'activeTab': "CALENDRIER"
    })

@login_required
def calendrier(request):
    if request.method == 'POST':
        pass

    return render(request, "", {
        'activeTab': "CALENDRIER"
    })

@login_required
def classements(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {
        'activeTab': "CLASSEMENT"
    })

@login_required
def tournois(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {
        'activeTab': "TOURNOI"
    })

@login_required
def archives(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {
        'activeTab': "ARCHIVE"
    })

@login_required()
def deconnexion_utilisateur(request):
    logout(request)
    return redirect("/Citrus/Connexion/?animation=2")

## THESE FUNCTIONS DONT BELONG HERE
## TO MOVE TO API
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
        teamID = data.get('teamID')



        equipe = Equipe.objects.get(id_equipe=teamID)
        for coach in Coach.objects.filter(equipe=equipe):
            if check_password(password, coach.password):
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




