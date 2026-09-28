# Checklist de déploiement — CITRUS

Liste priorisée des tâches à faire avant un déploiement en production, basée sur une analyse du code, des configs de déploiement, et des normes de sécurité/devops/maintenance.

## 🔴 Critique — bloquant avant toute mise en ligne

1. **Corriger le script de déploiement `.cpanel.yml`** — `cp * $DEPLOYPATH` copie seulement les fichiers à la racine sans `-r` : tous les dossiers (`CitrusApp/`, `LigueDesPamplemousseApp/`, `static/`, etc.) ne seront **jamais déployés**. Il faut un vrai script qui : copie récursivement en excluant `.git`, `.venv*`, `db.sqlite3`, `NOTPUBLIC.py`, `staticfiles/` ; lance `migrate` et `collectstatic` ; redémarre Passenger (`touch tmp/restart.txt`).
2. **Secrets en dur hors env vars** (`CitrusApp/NOTPUBLIC.py`) — `API_KEY` Google Maps, mot de passe SMTP, etc. sont codés en dur dans un fichier Python. Il n'est pas commité (bien géré via `.gitignore`), mais l'archi reste fragile — à migrer vers des variables d'environnement comme ça a déjà été fait pour `DJANGO_SECRET_KEY`. Pensez aussi à **restreindre la clé API Google** (referrer/IP) dans la console Google Cloud.
3. **URL de production incohérente dans les courriels** (`Helpers/EmailHelper.py:35`) — les liens (réinitialisation mdp, invitation coach, etc.) pointent vers `https://citrus.liguedespamplemousses.com` (sous-domaine), alors que le routing réel (`CITRUS/urls.py`) place le portail coach sous `liguedespamplemousses.com/Citrus/`. Si le sous-domaine n'existe pas, **tous les liens envoyés par courriel seront cassés**.
4. **Paramètres de sécurité Django manquants en production** (`CITRUS/settings.py`) — aucun de : `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_PROXY_SSL_HEADER` (nécessaire derrière Passenger/reverse proxy). À ajouter avant l'ouverture au public.
5. **Vérifier `DEBUG=False` en prod réel** — le défaut est bon (`os.environ.get('DJANGO_DEBUG') == '1'`), mais confirmez que la variable n'est *pas* accidentellement mise à `1` sur PlanetHoster.
6. **`db.sqlite3` en production** — SQLite convient pour un petit trafic, mais sur de l'hébergement mutualisé (accès concurrents faibles), assurez-vous d'avoir des **backups automatiques réguliers** (rien de visible actuellement) — une perte du fichier = perte de toute la ligue.

## 🟠 Important — devops / fiabilité

7. **Aucune CI configurée** (`.github` absent) — les tests existent (`CitrusApp/tests/`, `Citrus_api/tests.py`, `LigueDesPamplemousseApp/tests.py`) mais rien ne les exécute automatiquement. Ajoutez un workflow minimal (lint + `manage.py test`) sur chaque push/PR.
8. **Pages d'erreur personnalisées désactivées** — `handler404 = page_404` est **commenté** dans `CITRUS/urls.py`, et aucun `404.html`/`500.html` n'existe dans les templates. En prod (`DEBUG=False`), Django affichera la page d'erreur générique brute.
9. **Fichier de log commité dans git** (`CitrusApp/smtpLogs.txt`, actuellement vide mais tracké) — un fichier de log ne devrait pas être versionné (il va grossir et potentiellement contenir des adresses courriel). Ajoutez-le au `.gitignore` et supprimez-le du suivi (`git rm --cached`).
10. **Pas de `LOGGING` configuré** dans `settings.py`, et `Helpers/LogHelper.py` est un stub vide (`pass`) — aucune visibilité en cas d'erreur en prod. Configurez au minimum un logger fichier/console pour les erreurs 500.
11. **`TIME_ZONE = 'UTC'`** alors que la ligue est à Montréal/Québec — les heures de match affichées seront décalées de 4-5h. Passez à `America/Toronto` (ou `America/Montreal`).
12. **`LANGUAGE_CODE = 'en-us'`** alors que le site est 100% francophone (confirmé dans `PRODUCT.md`) — devrait être `fr-ca` pour le formatage correct des dates/nombres dans l'admin Django et les formulaires.
13. **WhiteNoise sans `STORAGES`/manifeste compressé** — la config actuelle fonctionne mais sans `CompressedManifestStaticFilesStorage`, vous perdez le cache-busting automatique des fichiers statiques (risque de cache navigateur périmé après chaque déploiement).
14. **47 appels `print()`** dans le code applicatif au lieu de `logging` — à nettoyer, ça pollue stdout et ne sera pas capturé correctement par Passenger.

## 🟡 Qualité de code / maintenance

15. **Incohérence de version Django** — `requirements.txt` fixe `Django==5.1.1`, mais `settings.py` référence encore la doc 4.2 dans ses commentaires (`# https://docs.djangoproject.com/en/4.2/...`). Pas bloquant, mais met à jour les commentaires ou vérifie que rien ne dépend d'un comportement 4.2.
16. **`CORS_ORIGIN_WHITELIST`** est le nom d'alias historique de `django-cors-headers` — le nom actuel recommandé est `CORS_ALLOWED_ORIGINS`.
17. **`CITRUS/urls.py` docstring dit "todelete project"** — reste d'un copier-coller du starter Django, à nettoyer.
18. **Logique d'authentification dans `CitrusApp/views/ajax.py:56`** (`any(check_password(password, c.password) for c in coachs)`) — mérite une relecture ciblée : vérifiez qu'il n'y a pas de risque d'énumération de comptes ou de logique d'auth ambiguë entre plusieurs coachs.
19. **Admin Django à l'URL par défaut `/admin/`** — pas grave en soi, mais assurez-vous que les comptes superuser ont des mots de passe forts et envisagez de limiter l'accès par IP si possible sur l'hébergement mutualisé.
20. **Aucun `robots.txt` ni `sitemap.xml`** pour le site public — utile pour le référencement d'un vrai site de ligue.

## 🟢 Contenu, légal, image de marque

21. **Aucun footer sur le site public** (`LigueDesPamplemousseApp/templates/.../base_public.html`) — il n'y a ni footer, ni mention légale, ni lien de contact en bas de page sur *aucune* page publique. À ajouter : coordonnées de la ligue, lien Contact, mentions légales/vie privée, crédit/copyright, réseaux sociaux si applicables.
22. **Politique de confidentialité / mentions légales absentes** — le site collecte potentiellement des données (inscriptions coachs, courriels, formulaire de contact) sans page de politique de confidentialité visible. Recommandé même pour un site amateur au Québec (Loi 25).
23. **Droit à l'image** — comme tu utilises ou prévois d'utiliser des photos de joueurs/coachs/événements sur le site public, prépare un **formulaire de consentement à l'image** signé par les participants (surtout si mineurs) avant publication, et ajoute une mention au règlement de la ligue précisant que des photos peuvent être prises et diffusées. Rien dans le code n'implémente ça (`CitrusApp/models.py` n'a pas de champ photo pour l'instant) — c'est une tâche de processus, pas de code, mais à faire *avant* de publier des photos réelles.
24. **Favicon manquant** — aucun favicon dédié au site (seul celui par défaut de Django REST Framework est présent dans `staticfiles/`).
25. **Gérer l'état "logos manquants"** — confirmé dans `PRODUCT.md` que `media/logos` est vide pour la plupart des équipes ; vérifie que le rendu reste propre visuellement (déjà noté comme contrainte de design, à valider visuellement avant lancement).
