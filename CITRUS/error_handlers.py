"""Pages d'erreur : une version pour CITRUS (connecté ou non), une pour le site de la Ligue.

Le site auquel appartient la requête est déterminé par le préfixe de l'URL :
/Citrus/ et /admin/ -> CITRUS, /api/ -> JSON, le reste -> site public de la Ligue.
"""
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from LigueDesPamplemousseApp.constants import DIVISION_SLUGS

ERREURS = {
    400: {
        "icone": "fa-triangle-exclamation",
        "titre": "Requête invalide",
        "message": "Votre demande n'a pas pu être traitée. Vérifiez l'adresse ou réessayez depuis l'accueil.",
    },
    403: {
        "icone": "fa-lock",
        "titre": "Vous n'avez pas accès à cette page",
        "message": "Vous n'avez pas les autorisations nécessaires pour consulter cette ressource. "
                   "Si vous pensez qu'il s'agit d'une erreur, contactez un administrateur.",
    },
    404: {
        "icone": "fa-compass",
        "titre": "Cette page n'existe pas",
        "message": "La page que vous cherchez a peut-être été déplacée ou supprimée. "
                   "Vérifiez l'adresse ou retournez à l'accueil.",
    },
    500: {
        "icone": "fa-circle-exclamation",
        "titre": "Une erreur est survenue",
        "message": "Quelque chose s'est mal passé de notre côté. Veuillez réessayer dans quelques instants.",
    },
}


def _site(request):
    chemin = request.path_info
    if chemin.startswith("/api/"):
        return "api"
    if chemin.startswith(("/Citrus/", "/admin/")) or chemin in ("/Citrus", "/admin"):
        return "citrus"
    return "ligue"


def _reponse(request, code):
    erreur = ERREURS[code]
    site = _site(request)

    if site == "api":
        return JsonResponse({"error": erreur["titre"]}, status=code)

    contexte = {"code": code, **erreur}

    if site == "citrus":
        # 500 : pas de base.html (nav, requêtes utilisateur) pour ne pas relancer une erreur.
        est_connecte = code != 500 and request.user.is_authenticated
        contexte["base_template"] = "base.html" if est_connecte else "erreurs/citrus_anonyme.html"
        return render(request, "erreurs/citrus.html", contexte, status=code)

    if code == 500:
        return render(request, "LigueDesPamplemousseApp/erreur_500.html", contexte, status=code)
    contexte.update(division_slugs=DIVISION_SLUGS, current_division_slug=None, tournoi_actif=False)
    return render(request, "LigueDesPamplemousseApp/erreur.html", contexte, status=code)


def _avec_secours(code):
    """Une page d'erreur ne doit jamais elle-même lever d'exception."""
    def vue(request, exception=None):
        try:
            return _reponse(request, code)
        except Exception:
            return HttpResponse(
                f"Erreur {code} : {ERREURS[code]['titre']}",
                status=code,
                content_type="text/plain; charset=utf-8",
            )
    return vue


bad_request = _avec_secours(400)
permission_denied = _avec_secours(403)
page_not_found = _avec_secours(404)
server_error = _avec_secours(500)
