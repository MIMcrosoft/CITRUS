import requests
from django.conf import settings

REQUEST_TIMEOUT_SECONDS = 5


class ClassementIndisponible(Exception):
    """Levée quand le classement ne peut pas être récupéré depuis Citrus_api."""


def _api_base_url():
    if settings.DEBUG:
        return "http://localhost:8000"
    return "https://citrus.liguedespamplemousses.com"


def get_classement(division, saison_id=None):
    """Récupère le classement d'une division depuis Citrus_api.

    `division` doit être la valeur exacte attendue par l'API
    (ex: "Pamplemousse"). `saison_id`, si fourni, filtre le classement
    sur cette saison (sinon l'API utilise la saison active).
    Retourne la liste `stats` triée par l'API.
    Lève ClassementIndisponible si l'API est injoignable, en erreur,
    ou renvoie une réponse invalide.
    """
    url = f"{_api_base_url()}/api/classement-{division}/"
    params = {"saison_id": saison_id} if saison_id else None

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        raise ClassementIndisponible("Impossible de contacter le service de classement.") from exc

    if response.status_code != 200:
        raise ClassementIndisponible(f"Le service de classement a répondu avec le code {response.status_code}.")

    try:
        data = response.json()
    except ValueError as exc:
        raise ClassementIndisponible("Réponse invalide du service de classement.") from exc

    if "stats" not in data:
        raise ClassementIndisponible("Réponse inattendue du service de classement.")

    return data["stats"]
