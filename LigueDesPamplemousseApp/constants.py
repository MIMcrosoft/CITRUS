from collections import OrderedDict

# Slug utilisé dans les URLs publiques -> valeur exacte stockée dans
# CitrusApp.models.Equipe.division / Match.division (DIVISION_CHOICES).
DIVISION_SLUGS = OrderedDict(
    [
        ("pamplemousse", "Pamplemousse"),
        ("tangerine", "Tangerine"),
        ("clementine", "Clementine"),
    ]
)
