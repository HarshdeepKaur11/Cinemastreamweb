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

# Database Repair Script: Manually add critical missing columns
echo "--- Running Database Repair Script ---"
python -c "
import os
import django
from django.db import connection
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinemastreamweb.settings')
django.setup()
with connection.cursor() as cursor:
    # List of columns to check/add in ml_models_movies
    cols = [
        ('poster_url_external', 'VARCHAR(2000)'),
        ('backdrop_url_external', 'VARCHAR(2000)'),
        ('poster', 'VARCHAR(255)'),
        ('backdrop', 'VARCHAR(255)'),
        ('created_at', 'DATETIME'),
        ('trailer_url', 'VARCHAR(255)'),
        ('content_rating', 'VARCHAR(50)'),
        ('dominant_color', 'VARCHAR(50)'),
        ('publisher', 'VARCHAR(255)'),
        ('content_descriptor', 'VARCHAR(255)')
    ]
    for col_name, col_type in cols:
        try:
            cursor.execute(f'SHOW COLUMNS FROM ml_models_movies LIKE \"{col_name}\"')
            if not cursor.fetchone():
                print(f'Adding missing column {col_name} to ml_models_movies...')
                cursor.execute(f'ALTER TABLE ml_models_movies ADD COLUMN {col_name} {col_type} NULL')
        except Exception as e:
            print(f'Error checking/adding {col_name}: {e}')
"

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
