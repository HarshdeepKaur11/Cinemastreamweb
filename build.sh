#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

# Force-fake the specific migrations that are already in the database
echo "--- Faking existing migrations ---"
python manage.py migrate ml_models 0002 --fake --noinput || echo "ml_models 0002 already faked or tables missing"
python manage.py migrate users 0001 --fake --noinput || echo "users 0001 already faked or tables missing"

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
