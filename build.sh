#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

echo "--- Running Migrations ---"
python manage.py showmigrations
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
