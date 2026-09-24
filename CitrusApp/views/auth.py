from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from ..functions import hash_code
from ..models import Coach, Equipe, Saison, Alignement
from Helpers.EmailHelper import EmailHelper


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

        return render(request, "admin/admin_gestion_utilisateurs.html", {
            'allUsers' : Coach.objects.all(),
            'saisonActive': Saison.objects.filter(est_active=True).first(),
            'domain' : domain,
            'activeTab': "USER"
        })

    else:
        return redirect("UserPage",current_user.coach_id)

@login_required
def profile_utilisateur(request, userID):
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
                return redirect("ConnexionUtilisateur")

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
            if coachToReset:
                code = str(coachToReset.prenom_coach) + str(coachToReset.nom_coach) + str(coachToReset.coach_id)
                emailHelper.courrielResetPwd(coachToReset.courriel,code)
                print("COURRIEL ENVOYÉ")

            return redirect('ConnexionUtilisateur')

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
        equipeCoach = Equipe.objects.get(id_equipe=coachTeamId)
        saisonActuelle = Saison.objects.get(est_active=True)
        alignementCoach = Alignement.objects.get(equipe=equipeCoach, saison=saisonActuelle)

        # Create the coach using CoachManager
        coach = Coach.objects.create_user(
            prenom_coach=coachPrenom,
            nom_coach=coachNom,
            pronom_coach=coachPronom,
            courriel=coachCourriel.strip().lower(),
            password=coachPassword,
            equipe=equipeCoach
        )

        alignementCoach.coachs.add(coach)

        emailHelper = EmailHelper()
        emailHelper.courrielConfirmationInscription(coach.courriel)

        return redirect('ConnexionUtilisateur')  # Assuming you have a login view

    # Render the signup form with all available teams
    return render(request, "inscription_coach.html", {
        'allEquipes': Equipe.objects.all(),
        'errors': errors
    })

@login_required()
def deconnexion_utilisateur(request):
    logout(request)
    return redirect("/Citrus/Connexion/?animation=2")
