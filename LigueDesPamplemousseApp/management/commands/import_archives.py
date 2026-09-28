"""Importe les archives des champions (Plaza + prix) depuis les trois
documents Word du dossier Archives/ à la racine du projet.

Ré-exécutable : chaque saison importée (division + saison_label) remplace
l'ArchiveAnnee existante plutôt que de la dupliquer.

Usage: python manage.py import_archives
"""
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from LigueDesPamplemousseApp.models import (
    ArchiveAnnee,
    ArchiveEquipe,
    ArchiveInterprete,
    ArchivePrix,
)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

FILES = {
    "Pamplemousse": "Liste des champions de la ligue des Pamplemousses.docx",
    "Tangerine": "Liste des champions de la ligue des Tangerines.docx",
    "Clementine": "Liste des champions de la ligue des Clementines.docx",
}

TEAM_HEADERS = {
    ArchiveEquipe.ROLE_CHAMPION_PLAZA: "Équipe Championne Plaza",
    ArchiveEquipe.ROLE_FINALISTE_PLAZA: "Équipe Finaliste Plaza",
    ArchiveEquipe.ROLE_CHAMPION_SAISON: "Équipe Championne de saison",
}

PRIZE_LABELS = [
    "Équipe sympathique",
    "Interprète construction",
    "Interprète Punch",
    "Recrue de l’année",
    "Interprète sympathique",
    "Équipe améliorée",
    "Interprète de l’année #1",
    "Interprète de l’année #2",
]

YEAR_RE = re.compile(r"^\d{4}-\d{4}$")
NONE_VALUES = {"-", "--", "—", "n/a", "aucun", "aucune"}
TEAM_LINE_RE = re.compile(r"\s[–-]\s")


def extract_paragraphs(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    tree = ElementTree.fromstring(xml)
    lines = []
    for p in tree.iter(W + "p"):
        texts = [t.text or "" for t in p.iter(W + "t")]
        line = "".join(texts)
        if line.strip():
            lines.append(line)
    return lines


def is_year(line):
    return bool(YEAR_RE.match(line))


def is_team_header(line):
    return line in TEAM_HEADERS.values()


def is_prize_label(line):
    for label in PRIZE_LABELS:
        if line.startswith(label):
            return label
    return None


def is_structural(line):
    return is_year(line) or is_team_header(line) or is_prize_label(line) is not None


def is_placeholder(line):
    return line.strip().lower() in NONE_VALUES


def looks_like_team_line(line):
    return bool(TEAM_LINE_RE.search(line))


def split_into_winners(extra):
    """Groupe une liste de lignes en paires (nom, equipe). Une ligne est
    rattachée au gagnant précédent comme équipe si elle contient un tiret
    séparateur ("Abrégé – Cégep") ; sinon elle démarre un nouveau gagnant."""
    winners = []
    current_name = None
    for line in extra:
        if looks_like_team_line(line):
            if current_name is not None:
                winners.append((current_name, line))
                current_name = None
            else:
                winners.append(("", line))
        else:
            if current_name is not None:
                winners.append((current_name, ""))
            current_name = line
    if current_name is not None:
        winners.append((current_name, ""))
    return winners


def parse_team_block(lines, i, warnings, year_label, division, role):
    n = len(lines)
    nom_equipe = ""
    cegep = ""

    pre = []
    while i < n and lines[i] != "A/C":
        if is_structural(lines[i]):
            warnings.append(
                f"{division} {year_label} [{role}]: ligne structurelle '{lines[i]}' "
                "rencontrée avant 'A/C' -- bloc équipe incomplet."
            )
            return {"nom_equipe": "", "cegep": "", "coach": "", "interpretes": []}, i
        pre.append(lines[i])
        i += 1
    pre = [p for p in pre if not is_placeholder(p)]
    if len(pre) == 1:
        nom_equipe = pre[0]
    elif len(pre) == 2:
        nom_equipe, cegep = pre
    elif len(pre) > 2:
        warnings.append(f"{division} {year_label} [{role}]: {len(pre)} lignes avant 'A/C' : {pre}")
        nom_equipe = " / ".join(pre)

    if i >= n or lines[i] != "A/C":
        warnings.append(f"{division} {year_label} [{role}]: 'A/C' attendu, obtenu {lines[i:i+1]}")
        return {"nom_equipe": nom_equipe, "cegep": cegep, "coach": "", "interpretes": []}, i
    i += 1
    if i < n and lines[i] == "Nom de l’interprète":
        i += 1

    interpretes = []
    coach = ""
    while i < n and lines[i] != "Coach":
        if is_structural(lines[i]):
            warnings.append(
                f"{division} {year_label} [{role}]: ligne structurelle '{lines[i]}' "
                "rencontrée avant 'Coach' -- roster incomplet."
            )
            return {"nom_equipe": nom_equipe, "cegep": cegep, "coach": "", "interpretes": interpretes}, i
        token = lines[i]
        if token in ("C", "A"):
            nxt = lines[i + 1] if i + 1 < n else None
            if nxt is not None and nxt not in ("C", "A", "Coach") and not is_structural(nxt) and not is_placeholder(nxt):
                interpretes.append((nxt, token))
                i += 2
            else:
                i += 1
        elif is_placeholder(token):
            i += 1
        else:
            interpretes.append((token, ""))
            i += 1

    if i < n and lines[i] == "Coach":
        i += 1
        if i < n and is_placeholder(lines[i]):
            i += 1
        elif i < n and not is_structural(lines[i]):
            coach = lines[i]
            i += 1

    return {"nom_equipe": nom_equipe, "cegep": cegep, "coach": coach, "interpretes": interpretes}, i


def parse_prizes(lines, i, warnings, year_label, division):
    n = len(lines)
    prizes = []
    for label in PRIZE_LABELS:
        if i >= n or not lines[i].startswith(label):
            warnings.append(f"{division} {year_label}: label de prix '{label}' attendu, obtenu {lines[i:i+1]}")
            continue
        i += 1
        extra = []
        while i < n and not is_prize_label(lines[i]) and not is_year(lines[i]) and lines[i] not in TEAM_HEADERS.values():
            extra.append(lines[i])
            i += 1
        extra = [e for e in extra if not is_placeholder(e)]
        for gagnant_nom, gagnant_equipe in split_into_winners(extra):
            prizes.append((label, gagnant_nom, gagnant_equipe))
    return prizes, i


def parse_file(path, warnings):
    lines = extract_paragraphs(path)

    division_line = lines[1]
    m = re.match(r"^Division (.+)$", division_line)
    division_raw = m.group(1) if m else "?"
    division_map = {"Pamplemousse": "Pamplemousse", "Tangerine": "Tangerine", "Clémentine": "Clementine"}
    division = division_map.get(division_raw, division_raw)

    i = 2
    n = len(lines)
    years = []
    seen_labels = set()
    while i < n:
        if not is_year(lines[i]):
            warnings.append(f"{division}: année attendue à l'index {i}, obtenu '{lines[i]}'")
            i += 1
            continue
        year_label = lines[i]
        i += 1
        if year_label in seen_labels:
            # Erreur de saisie constatée dans le document source (année copiée-collée
            # sans être mise à jour) : on décale d'une saison pour ne pas écraser
            # les données de la saison précédente au moment de l'import.
            start, end = (int(part) for part in year_label.split("-"))
            new_label = f"{start + 1}-{end + 1}"
            warnings.append(
                f"{division}: étiquette d'année '{year_label}' dupliquée dans le document -- "
                f"renommée en '{new_label}' (à vérifier/corriger dans l'admin si besoin)."
            )
            year_label = new_label
        seen_labels.add(year_label)
        annee_debut = int(year_label.split("-")[0])
        equipes = {}
        for role, header in TEAM_HEADERS.items():
            if i >= n or lines[i] != header:
                warnings.append(f"{division} {year_label}: en-tête '{header}' attendu, obtenu {lines[i:i+1]}")
                continue
            i += 1
            equipe, i = parse_team_block(lines, i, warnings, year_label, division, role)
            equipes[role] = equipe
        prizes, i = parse_prizes(lines, i, warnings, year_label, division)
        years.append(
            {
                "saison_label": year_label,
                "annee_debut": annee_debut,
                "equipes": equipes,
                "prix": prizes,
            }
        )
    return division, years


class Command(BaseCommand):
    help = "Importe les archives des champions depuis les fichiers Word du dossier Archives/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archives-dir",
            default=str(Path(settings.BASE_DIR) / "Archives"),
            help="Dossier contenant les 3 fichiers .docx (défaut: Archives/ à la racine du projet).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        archives_dir = Path(options["archives_dir"])
        warnings = []
        total_years = 0
        total_prix = 0
        total_interpretes = 0

        for division_key, filename in FILES.items():
            path = archives_dir / filename
            if not path.exists():
                raise CommandError(f"Fichier introuvable : {path}")

            division, years = parse_file(str(path), warnings)

            for year in years:
                annee, _ = ArchiveAnnee.objects.update_or_create(
                    division=division,
                    saison_label=year["saison_label"],
                    defaults={"annee_debut": year["annee_debut"]},
                )
                annee.equipes.all().delete()
                annee.prix.all().delete()

                for role, equipe_data in year["equipes"].items():
                    # On crée toujours les 3 rôles (même vides) pour que le titre du
                    # rôle reste affiché côté template quand une équipe n'est pas connue.
                    equipe = ArchiveEquipe.objects.create(
                        annee=annee,
                        role=role,
                        nom_equipe=equipe_data["nom_equipe"],
                        cegep=equipe_data["cegep"],
                        coach=equipe_data["coach"],
                    )
                    for ordre, (nom, role_interprete) in enumerate(equipe_data["interpretes"]):
                        role_label = {"C": "Capitaine", "A": "Assistant-capitaine"}.get(role_interprete, "")
                        ArchiveInterprete.objects.create(
                            equipe=equipe, nom=nom, role=role_label, ordre_affichage=ordre
                        )
                        total_interpretes += 1

                for ordre, (label, gagnant_nom, gagnant_equipe) in enumerate(year["prix"]):
                    ArchivePrix.objects.create(
                        annee=annee,
                        label=label,
                        gagnant_nom=gagnant_nom,
                        gagnant_equipe=gagnant_equipe,
                        ordre_affichage=ordre,
                    )
                    total_prix += 1

                total_years += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé : {total_years} saisons, {total_prix} prix, {total_interpretes} interprètes."
        ))
        if warnings:
            self.stdout.write(self.style.WARNING(f"{len(warnings)} avertissement(s) :"))
            for w in warnings:
                self.stdout.write(f"  - {w}")