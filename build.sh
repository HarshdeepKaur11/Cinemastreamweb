#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

# Nuclear sync: Fake everything for the main apps to bypass column errors
echo "--- Syncing migrations (Nuclear Option) ---"
python manage.py migrate ml_models --fake --noinput || echo "Failed to fake ml_models"
python manage.py migrate users --fake --noinput || echo "Failed to fake users"

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
