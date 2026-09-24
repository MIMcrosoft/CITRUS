from django.contrib import admin

from .models import (
    ArchiveAnnee,
    ArchiveEquipe,
    ArchiveInterprete,
    ArchivePrix,
    DocumentTelechargeable,
    MembreCA,
)


@admin.register(DocumentTelechargeable)
class DocumentTelechargeableAdmin(admin.ModelAdmin):
    list_display = ("titre", "categorie", "date_ajout")
    list_filter = ("categorie",)
    search_fields = ("titre",)


@admin.register(MembreCA)
class MembreCAAdmin(admin.ModelAdmin):
    list_display = ("nom", "poste", "courriel", "ordre_affichage")
    list_editable = ("ordre_affichage",)
    ordering = ("ordre_affichage",)


class ArchiveInterpreteInline(admin.TabularInline):
    model = ArchiveInterprete
    extra = 1
    fields = ("nom", "role", "ordre_affichage")


@admin.register(ArchiveEquipe)
class ArchiveEquipeAdmin(admin.ModelAdmin):
    list_display = ("annee", "role", "nom_equipe", "cegep", "coach")
    list_filter = ("annee__division", "role")
    search_fields = ("nom_equipe", "cegep", "coach")
    autocomplete_fields = ("annee",)
    inlines = [ArchiveInterpreteInline]


class ArchiveEquipeInline(admin.TabularInline):
    model = ArchiveEquipe
    extra = 0
    fields = ("role", "nom_equipe", "cegep", "coach")
    show_change_link = True


class ArchivePrixInline(admin.TabularInline):
    model = ArchivePrix
    extra = 1
    fields = ("label", "gagnant_nom", "gagnant_equipe", "ordre_affichage")


@admin.register(ArchiveAnnee)
class ArchiveAnneeAdmin(admin.ModelAdmin):
    list_display = ("saison_label", "division", "annee_debut")
    list_filter = ("division",)
    search_fields = ("saison_label",)
    ordering = ("division", "-annee_debut")
    inlines = [ArchiveEquipeInline, ArchivePrixInline]