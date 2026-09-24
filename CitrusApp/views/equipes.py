from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Coach, Equipe, College, Interprete, Saison, Alignement, Match, DetailsInterprete, DIVISION_CHOICES


@login_required
def gestion_equipes(request, id_saison=None):
    current_user = request.user
    saisonActive = Saison.objects.filter(est_active=True).first()

    if request.method == 'POST':
        pass
    if current_user.is_superuser == True:
        saisons = Saison.objects.all().order_by('-saison_id')
        if id_saison:
            saison_selectionnee = get_object_or_404(Saison, saison_id=id_saison)
        else:
            saison_selectionnee = saisonActive or saisons.first()

        allEquipes = Equipe.objects.all().order_by('nom_equipe')
        equipes_rows = [
            {
                'equipe': equipe,
                'division': equipe.get_division(saison_selectionnee) if saison_selectionnee else equipe.division,
                'est_active': equipe.is_active_pour_saison(saison_selectionnee) if saison_selectionnee else equipe.est_active,
            }
            for equipe in allEquipes
        ]

        return render(request, "admin/admin_equipes.html", {
            'equipes_rows': equipes_rows,
            'saisons': saisons,
            'saison_selectionnee': saison_selectionnee,
            'saisonActive': saisonActive,
            'division_choices': DIVISION_CHOICES,
            'activeTab': "EQUIPE"
        })
    else:
        return redirect('Equipe', current_user.information_equipe.id_equipe, 0)



@login_required
def information_equipe(request, id_equipe, id_saison=None):

    equipe = get_object_or_404(Equipe, id_equipe=id_equipe)

    if id_saison:
        saison = get_object_or_404(Saison, saison_id=id_saison)
    else:
        saison = Saison.objects.get(est_active=True)

    alignement = Alignement.objects.filter(equipe=equipe, saison=saison).first()

    if alignement:
        details_interpretes = DetailsInterprete.get_interpretes_triees(alignement)
        coachs = alignement.coachs.all()
        matchs = Match.objects.filter((Q(equipe1=equipe) | Q(equipe2=equipe)) & Q(saison=saison)).all()

    else:
        coachs = []
        matchs = None
        details_interpretes = None

    if request.method == 'POST':
        pass

    return render(request, "informations_equipe.html",
                  {'equipe': equipe,
                   'saisons': Saison.objects.all(),
                   'alignement': alignement,
                   'coachs': coachs,
                   'matchs_saisons' : matchs ,
                   'activeTab': "EQUIPE",
                   'current_user' : request.user,
                   'saison_selectionne' : saison,
                   'interpretes' : Interprete.objects.all().order_by('nom_interprete'),
                   'details_interpretes': details_interpretes,
                   })

@login_required
def equipe_ipp(request, id_equipe, id_saison=None):
    equipe = get_object_or_404(Equipe, id_equipe=id_equipe)

    if id_saison:
        saison = get_object_or_404(Saison, saison_id=id_saison)
    else:
        saison = Saison.objects.get(est_active=True)

    alignement = Alignement.objects.filter(equipe=equipe, saison=saison).first()

    if request.user in alignement.coachs.all():

        return render(request, "equipe_ipp.html", {
            'activeTab': "EQUIPE",
            'equipe': equipe,
            'alignement': alignement,
            'saison': saison,
            'saisons': Saison.objects.all(),
        })

    else:
        return render(request,"no_autorisation_page.html",
                      {
                          'activeTab': "EQUIPE",
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

        saisonActive = Saison.objects.filter(est_active=True).first()
        if saisonActive:
            Alignement.create_alignement(equipe=equipe, saison=saisonActive, division=divisionEquipe)

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

@login_required
def mes_equipes(request):
    current_user = request.user
    alignements = current_user.alignements.all()

    return render(request, "mes_equipes.html", {
        'alignements': alignements,
        'activeTab': "EQUIPE"
    })
