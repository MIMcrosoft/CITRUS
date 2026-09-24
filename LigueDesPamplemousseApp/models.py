from django.db import models

from .constants import DIVISION_SLUGS


class DocumentTelechargeable(models.Model):
    CATEGORIE_LIGUE = "ligue"
    CATEGORIE_PV = "pv"
    CATEGORIE_CHOICES = [
        (CATEGORIE_LIGUE, "Document de ligue"),
        (CATEGORIE_PV, "Procès-verbal"),
    ]

    titre = models.CharField(max_length=200)
    categorie = models.CharField(max_length=10, choices=CATEGORIE_CHOICES)
    fichier = models.FileField(upload_to="documents_ligue/")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_ajout"]

    def __str__(self):
        return self.titre


class MembreCA(models.Model):
    nom = models.CharField(max_length=100)
    poste = models.CharField(max_length=100)
    courriel = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="membres_ca/", blank=True, null=True)
    ordre_affichage = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre_affichage", "nom"]

    def __str__(self):
        return f"{self.nom} ({self.poste})"


class ArchiveAnnee(models.Model):
    """Une saison archivée (ex. 2012-2013) pour une division donnée."""

    division = models.CharField(max_length=20, choices=[(v, v) for v in DIVISION_SLUGS.values()])
    saison_label = models.CharField(max_length=20, help_text="Ex. 2012-2013")
    annee_debut = models.PositiveIntegerField(help_text="Sert au tri chronologique, ex. 2012")

    class Meta:
        ordering = ["division", "-annee_debut"]
        unique_together = ("division", "saison_label")
        verbose_name = "Année d'archive"
        verbose_name_plural = "Années d'archive"

    def __str__(self):
        return f"{self.division} — {self.saison_label}"


class ArchiveEquipe(models.Model):
    """Une équipe (championne Plaza, finaliste ou championne de saison) pour une ArchiveAnnee donnée."""

    ROLE_CHAMPION_PLAZA = "champion_plaza"
    ROLE_FINALISTE_PLAZA = "finaliste_plaza"
    ROLE_CHAMPION_SAISON = "champion_saison"
    ROLE_CHOICES = [
        (ROLE_CHAMPION_PLAZA, "Équipe championne (Plaza)"),
        (ROLE_FINALISTE_PLAZA, "Équipe finaliste (Plaza)"),
        (ROLE_CHAMPION_SAISON, "Équipe championne de saison"),
    ]
    ROLE_ORDRE = {ROLE_CHAMPION_PLAZA: 0, ROLE_FINALISTE_PLAZA: 1, ROLE_CHAMPION_SAISON: 2}

    annee = models.ForeignKey(ArchiveAnnee, related_name="equipes", on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    nom_equipe = models.CharField(max_length=100, blank=True)
    cegep = models.CharField(max_length=100, blank=True)
    coach = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Équipe d'archive"
        verbose_name_plural = "Équipes d'archive"

    def __str__(self):
        nom = self.nom_equipe or "?"
        return f"{self.get_role_display()} — {nom} ({self.annee.saison_label})"


class ArchiveInterprete(models.Model):
    """Un membre du roster d'une ArchiveEquipe (capitaine, assistant-capitaine ou joueur)."""

    equipe = models.ForeignKey(ArchiveEquipe, related_name="interpretes", on_delete=models.CASCADE)
    nom = models.CharField(max_length=150)
    role = models.CharField(max_length=30, blank=True, help_text="Ex. Capitaine, Assistant-capitaine")
    ordre_affichage = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre_affichage", "id"]
        verbose_name = "Interprète d'archive"
        verbose_name_plural = "Interprètes d'archive"

    def __str__(self):
        return self.nom


class ArchivePrix(models.Model):
    """Un prix remis lors d'une ArchiveAnnee. Le label est libre pour que les
    admins puissent ajouter facilement des prix custom en plus de ceux déjà
    importés (Recrue de l'année, Interprète Punch, etc.)."""

    annee = models.ForeignKey(ArchiveAnnee, related_name="prix", on_delete=models.CASCADE)
    label = models.CharField(max_length=150, help_text="Ex. Recrue de l'année")
    gagnant_nom = models.CharField(max_length=200, blank=True)
    gagnant_equipe = models.CharField(max_length=200, blank=True, help_text="Ex. MIM – Montmorency")
    ordre_affichage = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordre_affichage", "id"]
        verbose_name = "Prix d'archive"
        verbose_name_plural = "Prix d'archive"

    def __str__(self):
        return f"{self.label} — {self.gagnant_nom or '?'} ({self.annee.saison_label})"
