from django import template

register = template.Library()


@register.filter
def division_pour(equipe, saison):
    """Division de l'équipe pour la saison donnée (voir Equipe.get_division)."""
    if not equipe or not saison:
        return equipe.division if equipe else None
    return equipe.get_division(saison)


@register.filter
def est_active_pour(equipe, saison):
    """Statut actif/inactif de l'équipe pour la saison donnée (voir Equipe.is_active_pour_saison)."""
    if not equipe:
        return None
    if not saison:
        return equipe.est_active
    return equipe.is_active_pour_saison(saison)
