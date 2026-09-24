from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from CitrusApp.models import Alignement, Equipe, Match, Saison
from .constants import DIVISION_SLUGS
from .models import ArchiveAnnee, ArchiveEquipe, DocumentTelechargeable, MembreCA
from .services.citrus_api import ClassementIndisponible, get_classement

# Bascule simple pour activer l'onglet Tournoi plus tard, sans toucher aux templates.
TOURNOI_ACTIF = False


def _division_or_404(division_slug):
    if division_slug not in DIVISION_SLUGS:
        raise Http404("Division inconnue.")
    return DIVISION_SLUGS[division_slug]


def _nav_context(division_slug=None):
    return {
        "division_slugs": DIVISION_SLUGS,
        "current_division_slug": division_slug,
        "tournoi_actif": TOURNOI_ACTIF,
    }


def _archives_divisions():
    equipes_qs = ArchiveEquipe.objects.prefetch_related("interpretes")
    annees = ArchiveAnnee.objects.prefetch_related(
        Prefetch("equipes", queryset=equipes_qs), "prix"
    )

    saisons_par_nom = {nom: [] for nom in DIVISION_SLUGS.values()}
    for annee in annees:
        equipes_triees = sorted(
            annee.equipes.all(), key=lambda e: ArchiveEquipe.ROLE_ORDRE.get(e.role, 99)
        )
        saisons_par_nom.setdefault(annee.division, []).append(
            {"annee": annee, "equipes": equipes_triees, "prix": annee.prix.all()}
        )
    return [
        {"slug": slug, "nom": nom, "saisons": saisons_par_nom.get(nom, [])}
        for slug, nom in DIVISION_SLUGS.items()
    ]


def accueil(request):
    context = _nav_context()
    context["archives_divisions"] = _archives_divisions()
    return render(request, "LigueDesPamplemousseApp/accueil.html", context)


def calendrier(request, division):
    division_nom = _division_or_404(division)

    saisons = list(Saison.objects.order_by("-saison_id"))
    saison_id = request.GET.get("saison", "").strip()
    saison = next((s for s in saisons if str(s.saison_id) == saison_id), None)
    if saison is None:
        saison = next((s for s in saisons if s.est_active), None) or (saisons[0] if saisons else None)

    equipes = Equipe.objects.none()
    matchs = Match.objects.none()
    if saison is not None:
        equipes = Equipe.objects.filter(
            equipe__saison=saison, equipe__division=division_nom, equipe__est_active=True
        ).order_by("nom_equipe")

        equipes_inactives = set(
            Alignement.objects.filter(saison=saison, est_active=False).values_list("equipe_id", flat=True)
        )
        matchs = (
            Match.objects.filter(division=division_nom, saison=saison)
            .select_related("equipe1", "equipe2")
            .exclude(equipe1__isnull=True)
            .exclude(equipe2__isnull=True)
            .exclude(equipe1_id__in=equipes_inactives)
            .exclude(equipe2_id__in=equipes_inactives)
        )
    equipe_id = request.GET.get("equipe", "").strip()

    if equipe_id:
        try:
            equipe_id_int = int(equipe_id)
            matchs = matchs.filter(Q(equipe1_id=equipe_id_int) | Q(equipe2_id=equipe_id_int))
        except (ValueError, TypeError):
            equipe_id = ""

    matchs_a_venir = matchs.filter(completed_flag=False).order_by("date_match")
    matchs_joues = matchs.filter(completed_flag=True).order_by("-date_match")

    context = _nav_context(division)
    context.update(
        {
            "division_nom": division_nom,
            "saison": saison,
            "saisons": saisons,
            "saison_filtre": str(saison.saison_id) if saison else "",
            "equipes": equipes,
            "equipe_filtre": equipe_id,
            "matchs_a_venir": matchs_a_venir,
            "matchs_joues": matchs_joues,
        }
    )
    return render(request, "LigueDesPamplemousseApp/division/calendrier.html", context)


def equipes(request, division):
    division_nom = _division_or_404(division)
    saison = Saison.objects.filter(est_active=True).first()

    liste_equipes = Equipe.objects.none()
    if saison is not None:
        liste_equipes = Equipe.objects.filter(
            equipe__saison=saison, equipe__division=division_nom, equipe__est_active=True
        ).order_by("nom_equipe")

    context = _nav_context(division)
    context.update({"division_nom": division_nom, "saison": saison, "equipes": liste_equipes})
    return render(request, "LigueDesPamplemousseApp/division/equipes.html", context)


def equipe_detail(request, equipe_id):
    equipe = get_object_or_404(Equipe, id_equipe=equipe_id)
    saison = Saison.objects.filter(est_active=True).first()

    if saison is None or not equipe.is_active_pour_saison(saison):
        raise Http404("Équipe introuvable.")

    division_nom = equipe.get_division(saison)
    division_slug = next(
        (slug for slug, nom in DIVISION_SLUGS.items() if nom == division_nom), None
    )

    context = _nav_context(division_slug)
    context.update({"equipe": equipe, "division_nom": division_nom})
    return render(request, "LigueDesPamplemousseApp/division/equipe_detail.html", context)


def classement(request, division):
    division_nom = _division_or_404(division)

    saisons = list(Saison.objects.order_by("-saison_id"))
    saison_id = request.GET.get("saison", "").strip()
    saison = next((s for s in saisons if str(s.saison_id) == saison_id), None)
    if saison is None:
        saison = next((s for s in saisons if s.est_active), None) or (saisons[0] if saisons else None)

    stats = None
    erreur = None
    if saison is not None:
        try:
            stats = get_classement(division_nom, saison_id=saison.saison_id)
        except ClassementIndisponible:
            erreur = "Le classement est temporairement indisponible. Réessayez plus tard."

    context = _nav_context(division)
    context.update(
        {
            "division_nom": division_nom,
            "saison": saison,
            "saisons": saisons,
            "saison_filtre": str(saison.saison_id) if saison else "",
            "stats": stats,
            "erreur": erreur,
        }
    )
    return render(request, "LigueDesPamplemousseApp/division/classement.html", context)


def tournoi(request):
    context = _nav_context()
    return render(request, "LigueDesPamplemousseApp/tournoi.html", context)


def liens(request):
    documents = DocumentTelechargeable.objects.all()
    context = _nav_context()
    context.update(
        {
            "documents_ligue": documents.filter(categorie=DocumentTelechargeable.CATEGORIE_LIGUE),
            "proces_verbaux": documents.filter(categorie=DocumentTelechargeable.CATEGORIE_PV),
        }
    )
    return render(request, "LigueDesPamplemousseApp/liens.html", context)


def contact(request):
    membres = MembreCA.objects.all()
    context = _nav_context()
    context.update({"membres": membres})
    return render(request, "LigueDesPamplemousseApp/contact.html", context)
