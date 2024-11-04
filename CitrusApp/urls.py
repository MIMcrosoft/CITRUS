from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.accueil,name='Accueil'),
    path('Connexion/', views.loginUser, name='Connexion'),
    path('Calendrier/',views.calendrierAdmin,name='Calendrier'),
    path('components/', views.components,name='Components'),
    path('test/',views.test,name='Test'),
    path('Equipe<int:idEquipe>-<int:idSaison>/', views.equipe,name='Equipe'),
    path('Equipes/', views.allEquipes, name='Equipes'),
    path('AjoutEquipe/', views.ajoutEquipe, name='AjoutEquipe'),
    path('ModificationEquipe<int:idEquipe>/',views.modifEquipe, name='ModifEquipe'),
    path('AjoutInterprete<int:equipeId>-<int:alignementID>/',views.ajoutInterprete, name='AjoutInterprete'),
    path('ModificationInterprete<int:interpreteID>-<int:equipeID>/',views.modifInterprete, name='ModifInterprete'),
    path('Deconnexion/',views.log_out,name='Déconnexion'),
    path('Inscription/',views.coachSignUp,name='Inscription'),
    path('UserManagement/',views.users,name='UserManagement'),
    path('MonUser-<int:userID>/',views.userPage,name='UserPage'),
    path('ResetPassword-<str:hashedCoachID>/',views.resetPassword,name='ResetPassword'),
    path('Match-<str:hashedCode>/',views.match,name='Match'),
    path('MesMatchs/',views.matchs,name='matchs'),
    path('SaveToDB/',views.saveToDB,name='SaveToDB'),
    path('checkPassword/',views.checkPassword,name='checkPassword'),
    path('validateCoach/',views.validateCoach,name='validateCoach')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

