from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Coach, Equipe, College, Interprete, Saison, Alignements, Match,CoachManager
from .admin import CoachChangeForm
from django.views.decorators.http import require_POST
from .functions import *


def components(request):
    return render(request, 'components.html')

def test(request):
    return render(request, 'resetPasswordEmail.html')

"""

"""

@login_required
def accueil(request):
    current_user = request.user
    if current_user.is_superuser == True:
        allMatchs = Match.objects.all()
    else:
        equipe = current_user.equipe
        allMatchs = Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all()
    if request.method == 'POST':
        pass

    return render(request, 'Acceuil.html', {"user": current_user,
                                            'allMatchs': allMatchs,
                                            })


@login_required
def users(request):
    current_user = request.user
    if request.method == 'POST':
        pass

    if current_user.is_superuser == True:

        return render(request, "userManagement.html",{
            'allUsers' : Coach.objects.all()
        })

    else:
        return redirect("UserPage",current_user.coach_id)
"""

"""

@login_required
def userPage(request,userID):
    current_user = request.user
    if request.method == 'POST':
        pass

    return render(request,"userPage.html",{
        'user' : Coach.objects.get(coach_id=userID)
    })

def resetPassword(request,id):
    pass

def loginUser(request):
    if request.method == 'POST':

        buttonClicked = request.POST.get('button')

        if buttonClicked == 'connexion':

            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.validated_flag:
                login(request, user)
                return redirect('/Citrus/?animation=2')  # Redirect to home on successful login
            else:
                messages.error(request, 'Erreur')
                return redirect('connexion')  # Redirect to login page on error

        elif buttonClicked == 'resetPassword':
            email = request.POST['emailToReset']
            sendCoachEmail(email,EmailType.RESETPASSWORD)

        elif buttonClicked == "inscription":
            pass

    else:
        return render(request, "login.html", {})



"""

"""


def coachSignUp(request):
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
            return render(request, "coachSignUp.html", {
                'errors': errors,
                'allEquipes': Equipe.objects.all()
            })

        if Coach.objects.filter(courriel=coachCourriel).exists():
            errors.append('Un utilisateur avec ce courriel existe déja !')
            return render(request, "coachSignUp.html", {
                'errors': errors
            })

        # Retrieve the team from the database
        coachTeam = Equipe.objects.get(id_equipe=coachTeamId)

        # Create the coach using CoachManager
        coach = Coach.objects.create_user(
            prenom_coach=coachPrenom,
            nom_coach=coachNom,
            pronom_coach=coachPronom,
            courriel=coachCourriel,
            password=coachPassword,
            equipe=coachTeam
        )

        # Optionally redirect to a login or success page after successful signup
        return redirect('connexion')  # Assuming you have a login view

    # Render the signup form with all available teams
    return render(request, "coachSignUp.html", {
        'allEquipes': Equipe.objects.all(),
        'errors': errors
    })


"""

"""


@login_required
def allEquipes(request):
    current_user = request.user
    saisonActive = Saison.objects.get(est_active=True)
    if request.method == 'POST':
        pass
    if current_user.is_superuser == True:
        allEquipes = Equipe.objects.all()
        return render(request, "equipes.html", {'allEquipes': allEquipes, 'saisonActive': saisonActive})
    else:
        return redirect('equipe')


@login_required
def equipe(request, idEquipe, idSaison=None):
    current_user = request.user
    equipe = get_object_or_404(Equipe, id_equipe=idEquipe)
    alignement = None
    if idSaison:
        saison = get_object_or_404(Saison, saison_id=idSaison)
        alignement = Alignements.objects.filter(equipe=equipe, saison=saison).first()

        # Handle logic where both `equipe` and `saison` are used
    else:
        saison = Saison.objects.get(est_active=True)
        alignement = Alignements.objects.filter(equipe=equipe, saison=saison).first()

    if request.method == 'POST':
        pass

    return render(request, "equipe.html",
                  {'equipe': equipe,
                   'allSaisons': Saison.objects.all(),
                   'alignement': alignement,
                   'coachs': Coach.objects.filter(equipe=equipe),
                   'allMatchs' : Match.objects.filter(Q(equipe1=equipe) | Q(equipe2=equipe)).all()
                   })


@login_required
def modifEquipe(request, idEquipe):
    current_user = request.user
    equipe = get_object_or_404(Equipe, id_equipe=idEquipe)
    alignement = None
    if request.method == 'POST':
        newNomEquipe = request.POST.get('newNomEquipe')
        if newNomEquipe != None:
            newLogoEquipe = request.FILES['logoEquipe']
        # Ajouter un check erreur de Unique
        newCollegeID = request.POST.get('newCollegeEquipe')
        print(newCollegeID)

        equipe.nom_equipe = newNomEquipe
        equipe.college = College.objects.get(college_id=newCollegeID)
        equipe.logo = newLogoEquipe

        equipe.save()

        return redirect('equipe', equipe.id_equipe, 0)

    print(equipe.logo.url)
    return render(request, "equipeModif.html", {
        'equipe': equipe,
        'allSaisons': Saison.objects.all(),
        'alignement': alignement,
        'allColleges': College.objects.all()
    })


@login_required
def ajoutEquipe(request):
    if request.method == 'POST':
        nomEquipe = str(request.POST['nomEquipe'])
        divisionEquipe = str(request.POST['divisionEquipe'])
        logoEquipe = request.FILES['logoEquipe']
        collegeIDEquipe = int(request.POST['collegeEquipe'])
        coachIDEquipe = int(request.POST['coachEquipe'])
        # indispoEquipe

        print(nomEquipe, divisionEquipe, collegeIDEquipe, coachIDEquipe)
        collegeEquipe = College.objects.get(college_id=collegeIDEquipe)
        coach = Coach.objects.get(coach_id=coachIDEquipe)

        equipe = Equipe.createEquipe(
            nomEquipe=nomEquipe,
            logo=logoEquipe,
            division=divisionEquipe,
            college=collegeEquipe
        )

        coach.equipe = equipe
        coach.save()

        return redirect('equipes')
    current_user = request.user
    allColleges = College.objects.all()
    allCoachs = Coach.objects.all()
    if current_user.is_superuser == True:
        return render(request, "ajoutEquipe.html", {'allColleges': allColleges, 'allCoachs': allCoachs})


@login_required
def ajoutInterprete(request, equipeId, alignementID):
    allInterpretes = Interprete.objects.all()
    if request.method == 'POST':
        nomInterprete = request.POST['nomInterprete']
        pronomsInterprete = request.POST['pronomsInterprete']
        numInterprete = request.POST['numInterprete']
        # Role
        roleInterprete = request.POST.get('radioRoleInterprete')

        alignement = Alignements.objects.get(id_alignement=alignementID)

        interprete = Interprete.createInterprete(
            nom_interprete=nomInterprete,
            pronom_interprete=pronomsInterprete,
            numero_interprete=numInterprete,
            role_interprete=roleInterprete,
            alignement=alignement
        )
        interprete.save()

    return render(request, "ajoutInterprete.html",
                  {
                      'equipe': Equipe.objects.get(id_equipe=equipeId),
                      'alignement': Alignements.objects.get(id_alignement=alignementID),
                      'allInterpretes': allInterpretes,
                      'modifyFlag': False
                  })


@login_required
def modifInterprete(request, interpreteID, equipeID):
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

        return redirect('equipe',equipeID,0)

    return render(request, "ajoutInterprete.html", {
        'equipe': Equipe.objects.get(id_equipe=equipeID),
        'interprete' : Interprete.objects.get(interprete_id=interpreteID),
        'allInterpretes': allInterpretes,
        'modifyFlag' : True
    })


"""
calendrierAdmin
Page que l'admin va voir afin de créer ou de charger un calendrier
"""


@login_required
def calendrierAdmin(request):
    if request.method == 'POST':
        pass

    return render(request, "calendrier/calendrier-step0.html", {})


"""
calendrier
Page que les coachs vont voir lorsqu'il veulent voir le calendrier des matchs
"""


@login_required
def calendrier(request):
    if request.method == 'POST':
        pass

    return render(request, "", {})


"""

"""


@login_required
def classements(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


@login_required
def tournois(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


@login_required
def archives(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


@login_required()
def log_out(request):
    logout(request)
    return redirect("/Citrus/Connexion/?animation=2")
