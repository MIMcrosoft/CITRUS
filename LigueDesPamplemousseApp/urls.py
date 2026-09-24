from django.urls import path

from . import views

app_name = "ligue"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("<str:division>/Calendrier/", views.calendrier, name="calendrier"),
    path("<str:division>/Equipes/", views.equipes, name="equipes"),
    path("Equipe-<int:equipe_id>/", views.equipe_detail, name="equipe_detail"),
    path("<str:division>/Classement/", views.classement, name="classement"),
    path("Tournoi/", views.tournoi, name="tournoi"),
    path("Liens/", views.liens, name="liens"),
    path("Contact/", views.contact, name="contact"),
]
