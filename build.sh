#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

# Ultimate Nuclear Sync: Fake all apps
echo "--- Syncing migrations (Ultimate Nuclear Option) ---"
APPS=("ml_models" "users" "admin_panel" "core" "dashboard")
for app in "${APPS[@]}"; do
    python manage.py migrate $app --fake --noinput || echo "Failed to fake $app"
done

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
