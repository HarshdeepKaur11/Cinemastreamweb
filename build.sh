#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Dependencies ---"
pip install -r requirements.txt

# Smart Migration: Try normal migrate first, fake only if tables exist
echo "--- Running Smart Migrations ---"
APPS=("contenttypes" "auth" "admin" "sessions" "messages" "staticfiles" "ml_models" "users" "admin_panel" "core" "dashboard")

for app in "${APPS[@]}"; do
    echo "Syncing $app..."
    # Try to migrate normally. If it fails with 'already exists' (1050), then fake it.
    python manage.py migrate $app --noinput 2>/tmp/migrate_error || true
    if grep -q "1050" /tmp/migrate_error; then
        echo "Table exists for $app, faking..."
        python manage.py migrate $app --fake --noinput
    elif [ -s /tmp/migrate_error ]; then
        echo "Error in $app, but continuing: $(cat /tmp/migrate_error)"
    fi
done

# Run any remaining global migrations
python manage.py migrate --noinput --fake-initial || python manage.py migrate --noinput --fake

# Master Database Repair Script: Manually sync TiDB with Django models
echo "--- Running Master Database Repair Script ---"
python -c "
import os
import django
from django.db import connection
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinemastreamweb.settings')
django.setup()
with connection.cursor() as cursor:
    # 1. Fix ml_models_movies
    movies_cols = [
        ('duration_minutes', 'INT'),
        ('poster_url_external', 'VARCHAR(2000)'),
        ('backdrop_url_external', 'VARCHAR(2000)'),
        ('created_at', 'DATETIME'),
        ('trailer_url', 'VARCHAR(255)'),
        ('content_rating', 'VARCHAR(50)'),
        ('publisher', 'VARCHAR(255)'),
        ('content_descriptor', 'TEXT'),
        ('dominant_color', 'VARCHAR(50)')
    ]
    for col_name, col_type in movies_cols:
        try:
            cursor.execute(f'SHOW COLUMNS FROM ml_models_movies LIKE \"{col_name}\"')
            if not cursor.fetchone():
                print(f'Repair: Adding {col_name} to ml_models_movies')
                cursor.execute(f'ALTER TABLE ml_models_movies ADD COLUMN {col_name} {col_type} NULL')
        except Exception as e: print(f'Skipping {col_name}: {e}')

    # 2. Fix ml_models_genre (ensure name column exists)
    try:
        cursor.execute('SHOW COLUMNS FROM ml_models_genre LIKE \"name\"')
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE ml_models_genre ADD COLUMN name VARCHAR(100) NULL')
    except Exception as e: print(f'Genre fix error: {e}')

    # 3. Fix ml_models table
    ml_cols = [('trained_on', 'DATETIME'), ('version', 'INT')]
    for col_name, col_type in ml_cols:
        try:
            cursor.execute(f'SHOW COLUMNS FROM ml_models LIKE \"{col_name}\"')
            if not cursor.fetchone():
                cursor.execute(f'ALTER TABLE ml_models ADD COLUMN {col_name} {col_type} NULL')
        except Exception as e: print(f'ML fix error: {e}')
"

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
