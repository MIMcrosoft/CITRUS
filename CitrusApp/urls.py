from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.accueil,name='accueil'),
    path('Connexion/', views.loginUser, name='login'),
    path('CoachSignIn<int:id>/', views.coachSignIn, name='coach_sign_in'),
    path('Calendrier/',views.calendrierAdmin,name='calendrier'),
    path('test/', views.components,name='components'),
    path('Equipe<int:idEquipe>-<int:idSaison>/', views.equipe,name='equipe'),
    path('Equipes/', views.allEquipes, name='equipes'),
    path('AjoutEquipe/', views.ajoutEquipe, name='ajoutEquipe'),
    path('ModificationEquipe<int:idEquipe>/',views.modifEquipe, name='modifEquipe'),
    path('AjoutInterprete<int:equipeId>-<int:alignementID>/',views.ajoutInterprete, name='ajoutInterprete'),
    path('ModificationInterprete<int:interpreteID>-<int:equipeID>/',views.modifInterprete, name='modifInterprete')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

