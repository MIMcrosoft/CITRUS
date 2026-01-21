from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('classement-<str:division>/',views.classement,name='Classement'),
    path('get-pronom-interprete-<int:interprete_id>', views.get_pronoms_interprete, name='getPronomsInterprete'),
    path("creer_interprete", views.creer_interprete, name='creerInterprete'),
    path("ajouter_interprete_alignement",views.ajouter_interprete_alignement, name='ajouterInterpreteAlignment'),
    path("modifier_interprete", views.modifier_interprete, name='modifierInterprete'),
    path("creer_requete_report_match/", views.creer_requete_report_match, name='creerRequeteReportMatch'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

