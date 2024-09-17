from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.accueil,name='accueil'),
    path('Connexion/', views.loginUser, name='connexion'),
    path('Calendrier/',views.calendrierAdmin,name='calendrier'),
    path('components/', views.components,name='components'),
    path('test/',views.test,name='test'),
    path('Equipe<int:idEquipe>-<int:idSaison>/', views.equipe,name='equipe'),
    path('Equipes/', views.allEquipes, name='equipes'),
    path('AjoutEquipe/', views.ajoutEquipe, name='ajoutEquipe'),
    path('ModificationEquipe<int:idEquipe>/',views.modifEquipe, name='modifEquipe'),
    path('AjoutInterprete<int:equipeId>-<int:alignementID>/',views.ajoutInterprete, name='ajoutInterprete'),
    path('ModificationInterprete<int:interpreteID>-<int:equipeID>/',views.modifInterprete, name='modifInterprete'),
    path('Deconnexion/',views.log_out,name='Déconnexion'),
    path('Inscription/',views.coachSignUp,name='Inscription')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

