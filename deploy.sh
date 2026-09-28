#!/bin/bash
set -euo pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD)

case "$BRANCH" in
  dev)
    APP=dev
    ;;
  citrus|main)
    APP=citrus
    ;;
  *)
    echo "Branche '$BRANCH' non prévue, déploiement annulé." >&2
    exit 1
    ;;
esac

PYVER=3.10
DEPLOYPATH="$HOME/$APP"
VENV="$HOME/virtualenv/$APP/$PYVER/bin/activate"

echo "Déploiement de '$BRANCH' vers $DEPLOYPATH"

# 1. Copie récursive
/bin/rsync -a \
  --exclude='.git' --exclude='.venv*' --exclude='db.sqlite3' \
  --exclude='.env' --exclude='staticfiles/' --exclude='__pycache__/' \
  --exclude='.cpanel.yml' --exclude='deploy.sh' --exclude='tmp/' \
  ./ "$DEPLOYPATH/"

# 2. Dépendances, migrations, statiques
cd "$DEPLOYPATH"
source "$VENV"
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# 3. Redémarrage de Passenger
mkdir -p tmp
touch tmp/restart.txt