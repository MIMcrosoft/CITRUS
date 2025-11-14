from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.accueil, name='Accueil'),
    path('Connexion/', views.connexion_utilisateur, name='ConnexionUtilisateur'),
    path('Calendrier/',views.calendrierAdmin,name='CalendrierAdmin'),
    path('Composants/', views.composants_html, name='ComposantsHtml'),
    path('test/',views.test,name='Test'),
    path('Equipe<int:id_equipe>-<int:id_saison>/', views.information_equipe, name='InformationsEquipe'),
    path('Equipes/', views.gestion_equipes, name='GestionEquipes'),
    path('AjoutEquipe/', views.ajout_equipe, name='AjoutEquipe'),
    path('ModificationEquipe<int:idEquipe>/', views.modification_equipe, name='ModificationEquipe'),
    path('AjoutInterprete-<int:alignementID>/', views.ajout_interprete, name='AjoutInterprete'),
    path('ModificationInterprete<int:interpreteID>-<int:equipeID>/', views.modification_interprete, name='ModificationInterprete'),
    path('Deconnexion/', views.deconnexion_utilisateur, name='DeconnexionUtilisateur'),
    path('Inscription/', views.inscription_coach, name='InscriptionCoach'),
    path('UserManagement/', views.gestion_utilisateurs, name='GestionUtilisateur'),
    path('MonUser-<int:userID>/', views.profile_utilisateur, name='ProfileUtilisateur'),
    path('ResetPassword-<str:hashedCoachID>/', views.reinitialisation_mdp, name='ReinitialisationMdp'),
    path('Match-<str:hashedCode>/', views.formulaire_match, name='FormulaireMatch'),
    path('MesMatchs/', views.mes_matchs, name='MesMatchs'),
    path('MesMatchs-<int:id_saison>/',views.mes_matchs,name='MesMatchs'),
    path('SaveToDB/',views.saveToDB,name='SaveToDB'),
    path('checkPassword/',views.checkPassword,name='checkPassword'),
    path('validateCoach/',views.validateCoach,name='validateCoach'),
    path('FicheCodeQR-<int:equipeId>-<int:saisonId>/', views.fiche_code_QR, name='FicheCodeQR'),
    path('formulaire-report-match', views.reporter_match, name='reporterMatch'),
    path('MesÉquipes', views.mes_equipes, name='MesEquipes'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

