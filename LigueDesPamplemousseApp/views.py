import re
import unicodedata

from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from CitrusApp.models import Alignement, DetailsInterprete, Equipe, Match, Saison
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


def _normaliser_nom(nom):
    """Clé de comparaison tolérante : sans accents, casse, ponctuation ni « s » final
    (« Portes-Patios » et « Portes Patio » donnent la même clé)."""
    texte = unicodedata.normalize("NFKD", nom or "")
    texte = "".join(c for c in texte if not unicodedata.combining(c)).lower()
    texte = re.sub(r"[^a-z0-9]", "", texte)
    return texte[:-1] if texte.endswith("s") and len(texte) > 3 else texte


def _nom_equipe_du_prix(gagnant_equipe):
    """« MIM – Montmorency » -> « MIM » (le texte libre sépare équipe et cégep par un tiret)."""
    return re.split(r"\s+[–—-]\s+", gagnant_equipe or "", maxsplit=1)[0]


def _historique_equipe(equipe):
    """Titres et prix de l'équipe dans les archives, rattachés par le nom d'équipe
    (les archives ne contiennent pas de clé vers Equipe)."""
    cle = _normaliser_nom(equipe.nom_equipe)
    if not cle:
        return None

    annees = ArchiveAnnee.objects.prefetch_related(
        Prefetch("equipes", queryset=ArchiveEquipe.objects.prefetch_related("interpretes")),
        "prix",
    ).order_by("-annee_debut", "division")

    saisons = []
    totaux = {"champion_plaza": 0, "finaliste_plaza": 0, "champion_saison": 0, "prix": 0}
    for annee in annees:
        titres = [
            e for e in sorted(annee.equipes.all(), key=lambda e: ArchiveEquipe.ROLE_ORDRE.get(e.role, 99))
            if _normaliser_nom(e.nom_equipe) == cle
        ]
        prix = [
            p for p in annee.prix.all()
            if _normaliser_nom(_nom_equipe_du_prix(p.gagnant_equipe)) == cle
        ]
        if not titres and not prix:
            continue
        for t in titres:
            totaux[t.role] = totaux.get(t.role, 0) + 1
        totaux["prix"] += len(prix)
        saisons.append({"annee": annee, "titres": titres, "prix": prix})

    if not saisons:
        return None
    # Une finale = toute apparition en finale Plaza, qu'elle soit gagnée ou perdue.
    totaux["finales_plaza"] = totaux["champion_plaza"] + totaux["finaliste_plaza"]
    return {"saisons": saisons, "totaux": totaux}


def _alignement_equipe(equipe, saison):
    alignement = equipe.get_alignement(saison)
    if alignement is None:
        return []
    ordre = {"C": 0, "A": 1}  # capitaine, puis assistants, puis le reste par numéro

    def cle(details):
        numero = details.numero_interprete or ""
        return (ordre.get(details.role_interprete, 2), int(numero) if numero.isdigit() else 10**6, numero)

    return sorted(DetailsInterprete.get_interpretes_triees(alignement), key=cle)


def _matchs_joues_equipe(equipe, saison):
    matchs = (
        Match.objects.filter(saison=saison, completed_flag=True)
        .filter(Q(equipe1=equipe) | Q(equipe2=equipe))
        .select_related("equipe1", "equipe2", "equipe1__college")
        .order_by("-date_match")
    )
    resultats = []
    bilan = {"victoires": 0, "defaites": 0, "nuls": 0}
    for match in matchs:
        if match.equipe1_id is None or match.equipe2_id is None:
            continue
        a_domicile = match.equipe1_id == equipe.id_equipe
        pour, contre = (match.score_eq1, match.score_eq2) if a_domicile else (match.score_eq2, match.score_eq1)
        if pour > contre:
            issue, cle = "V", "victoires"
        elif pour < contre:
            issue, cle = "D", "defaites"
        else:
            issue, cle = "N", "nuls"
        bilan[cle] += 1
        resultats.append(
            {
                "match": match,
                "adversaire": match.equipe2 if a_domicile else match.equipe1,
                "a_domicile": a_domicile,
                "pour": pour,
                "contre": contre,
                "issue": issue,
            }
        )
    return resultats, bilan


def equipe_detail(request, equipe_id):
    equipe = get_object_or_404(Equipe, id_equipe=equipe_id)
    saison = Saison.objects.filter(est_active=True).first()

    if saison is None or not equipe.is_active_pour_saison(saison):
        raise Http404("Équipe introuvable.")

    division_nom = equipe.get_division(saison)
    division_slug = next(
        (slug for slug, nom in DIVISION_SLUGS.items() if nom == division_nom), None
    )

    matchs_joues, bilan = _matchs_joues_equipe(equipe, saison)

    context = _nav_context(division_slug)
    context.update(
        {
            "equipe": equipe,
            "division_nom": division_nom,
            "saison": saison,
            "alignement": _alignement_equipe(equipe, saison),
            "matchs_joues": matchs_joues,
            "bilan": bilan,
            "historique": _historique_equipe(equipe),
        }
    )
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
