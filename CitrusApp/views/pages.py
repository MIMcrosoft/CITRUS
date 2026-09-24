from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect

from ..models import Saison, Alignement, Match, Equipe


def composants_html(request):
    return render(request, 'composants_individuels.html')

def test(request):
    return render(request, 'templatesCourriel/email_report_match_accepte.html')

def page_404(request,exception):
    return render(request, 'fenetre_erreur.html', {
        'errorMsg': "Oups Cette page n'existe pas !"
    })

def accueil(request):
    premiere_connexion = False
    current_user = request.user
    saison = Saison.objects.get(est_active=True)
    equipes = Equipe.objects.all()
    if isinstance(current_user, AnonymousUser) or not current_user.is_authenticated:
        # Redirect or handle the case when the user is not logged in
        return redirect('ConnexionUtilisateur')

    if not current_user.est_coach_cette_saison(saison.saison_id):
        premiere_connexion = True

    if current_user.is_superuser == True:
        matchs = Match.objects.all()
    else:
        alignement = Alignement.objects.filter(Q(saison=saison) & Q(coachs=current_user)).first()
        equipe = alignement.equipe
        matchs = Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all()

    if request.method == 'POST':
        pass

    return render(request, 'accueil.html', {
        "user": current_user,
        'matchs': matchs,
        'activeTab' : "ACCUEIL",
        'equipes' : equipes,
        'premiere_connexion' : premiere_connexion
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
