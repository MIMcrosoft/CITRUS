from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.shortcuts import render, redirect

from ..functions import hash_code
from ..models import Saison, Alignement, Match, Equipe, Punition, DetailsInterprete, RequeteReportMatch
from Helpers.EmailHelper import EmailHelper


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

    try:
        alignement = Alignement.objects.filter(Q(saison=saison) & Q(coachs=current_user)).first()
        equipe = alignement.equipe
        matchs = Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all()

    except Alignement.DoesNotExist:
        equipe = None
        matchs = Match.objects.none()



    return render(request, "mes_matchs.html", {
        'current_user' : current_user,
        'equipe': equipe,
        'saisons' : Saison.objects.all(),
        'saison_selectionne' : saison,
        'matchs' : matchs,
        'activeTab': "MATCH",
    })

@login_required()
def demande_report_match(request, demandeToken):

    rr = RequeteReportMatch.objects.get(token=demandeToken)
    current_user = request.user
    emailHelper = EmailHelper()

    if request.method == 'POST':
        choice = request.POST.get('choice')
        date_str  = request.POST.get('nouvelle_date')
        if choice == "accepter":

            if current_user.coach_id == rr.coach_1.coach_id:
                rr.coach1_validation = True

            if current_user.coach_id == rr.coach_2.coach_id:
                rr.coach2_validation = True

            if current_user.admin_flag:
                rr.admin_validation = True

            if rr.coach1_validation and rr.coach2_validation and rr.admin_validation:
                rr.match.date_match = rr.nouvelle_date
                rr.status = "approuve"
                rr.save()
                rr.match.save()
                emailHelper.courrielReportMatchAccepte(
                    rr.coach_1.courriel,
                    rr.coach_2.courriel,
                    EmailHelper.COURRIEL_ADMIN,
                    EmailHelper.COURRIEL_RESPO_COM,
                    rr
                )

            else:
                rr.save()
                emailHelper.courrielUpdateReportMatch(
                    rr.coach_1.courriel,
                    rr.coach_2.courriel,
                    EmailHelper.COURRIEL_ADMIN,
                    rr
                )

            return redirect('ConnexionUtilisateur')

        if choice == "decliner":

            if date_str is None or date_str == "":
                messages.error(request, "Veuillez sélectionner une nouvelle date.")
                return redirect(request.path)

            nouvelle_date = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')

            rr.coach1_validation = False
            rr.coach2_validation = False
            rr.admin_validation = False

            if current_user.coach_id == rr.coach_1.coach_id:
                rr.coach1_validation = True

            if current_user.coach_id == rr.coach_2.coach_id:
                rr.coach2_validation = True

            if current_user.admin_flag:
                rr.admin_validation = True

            rr.nouvelle_date = nouvelle_date
            rr.save()
            emailHelper.courrielUpdateReportMatch(
                rr.coach_1.courriel,
                rr.coach_2.courriel,
                EmailHelper.COURRIEL_ADMIN,
                rr
            )
            messages.success(request, "Votre réponse a été enregistrée.")
            return redirect('ConnexionUtilisateur')


    coach_complete = False
    if current_user == rr.coach_1 and rr.coach1_validation:
        coach_complete = True
    elif current_user == rr.coach_2 and rr.coach2_validation:
        coach_complete = True

    return render(request, "demande_report_match.html",{
        "requete" : rr,
        "coach_complete" : coach_complete,
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
                print(punition)
                equipe = Equipe.objects.get((Q(id_equipe=matchSelected.equipe1.id_equipe) | Q(id_equipe=matchSelected.equipe2.id_equipe)) & Q(nom_equipe=punition['equipe']))
                if punition['majeure'] == "Oui":
                    est_majeure = True
                else:
                    est_majeure = False

                Punition.createPunition(punition['titre'],est_majeure,equipe)
        matchSelected.save()

        alignementEq1 = Alignement.objects.get(equipe=matchSelected.equipe1, saison=matchSelected.saison)
        coachEq1 = alignementEq1.coachs.first()

        alignementEq2 = Alignement.objects.get(equipe=matchSelected.equipe2, saison=matchSelected.saison)
        coachEq2 = alignementEq2.coachs.first()

        if not TEST and not settings.DEBUG:
            emailHelper = EmailHelper()
            emailHelper.courrielResumeMatch(
                coachEq1.courriel if coachEq1 else None,
                coachEq2.courriel if coachEq2 else None,
                matchSelected
            )

    if matchSelected is not None:
        saison = Saison.objects.get(est_active=True)
        alignementEquipe1 = Alignement.objects.filter(equipe=matchSelected.equipe1, saison=saison).first()
        detailsInterpretesEq1 = DetailsInterprete.get_interpretes_triees(alignementEquipe1)
        coachEquipe1 = alignementEquipe1.coachs.first() if alignementEquipe1 else None

        alignementEquipe2 = Alignement.objects.filter(equipe=matchSelected.equipe2, saison=saison).first()
        detailsInterpretesEq2 = DetailsInterprete.get_interpretes_triees(alignementEquipe2)
        coachEquipe2 = alignementEquipe2.coachs.first() if alignementEquipe2 else None

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

@login_required()
def admin_matchs(request, id_saison=None):
    current_user = request.user
    if current_user.admin_flag:
        if id_saison is None:
            saison = Saison.objects.get(est_active=True)
        else:
            try:
                saison = Saison.objects.get(saison_id=id_saison)
            except Saison.DoesNotExist:
                saison = Saison.objects.get(est_active=True)
                return redirect('AdminMatchs', saison.saison_id)

        return render(request, "admin/admin_matchs.html", {
            'saisons': Saison.objects.all(),
            'saison_selectionne': saison,
            'matchs': Match.objects.filter(saison=saison).all(),
            'activeTab': "MATCH",
        })
    else:
        return redirect('/Citrus/Accueil')
