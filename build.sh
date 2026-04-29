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

def table_exists(cursor, table_name):
    cursor.execute(f\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'\")
    return cursor.fetchone()[0] > 0

def get_columns(cursor, table_name):
    cursor.execute(f\"SELECT COLUMN_NAME FROM information_schema.columns WHERE table_name = '{table_name}'\")
    return [row[0] for row in cursor.fetchall()]

with connection.cursor() as cursor:
    print('--- Starting Repair Logic ---')
    
    # 1. Fix ml_models_genre
    try:
        cursor.execute('DESCRIBE ml_models_genre')
        cols = [row[0].lower() for row in cursor.fetchall()]
        print(f'DEBUG: ml_models_genre columns found: {cols}')
        if 'name' not in cols:
            if 'genre_name' in cols:
                print('Repair: Renaming genre_name to name in ml_models_genre')
                cursor.execute('ALTER TABLE ml_models_genre RENAME COLUMN genre_name TO name')
            else:
                print('Repair: Adding name column to ml_models_genre')
                cursor.execute('ALTER TABLE ml_models_genre ADD COLUMN name VARCHAR(100) NULL')
        
        # FINAL FIX: If both exist, drop genre_name to avoid loaddata failure
        if 'name' in cols and 'genre_name' in cols:
            print('Repair: Dropping redundant genre_name from ml_models_genre')
            cursor.execute('ALTER TABLE ml_models_genre DROP COLUMN genre_name')
        else:
            print('DEBUG: ml_models_genre already has \"name\" column.')
    except Exception as e: print(f'DEBUG: Genre fix failed: {e}')

    # 2. Fix ml_models_movies
    try:
        cursor.execute('DESCRIBE ml_models_movies')
        cols = [row[0].lower() for row in cursor.fetchall()]
        print(f'DEBUG: ml_models_movies columns found: {cols}')
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
            if col_name.lower() not in cols:
                print(f'Repair: Adding {col_name} to ml_models_movies')
                cursor.execute(f'ALTER TABLE ml_models_movies ADD COLUMN {col_name} {col_type} NULL')
    except Exception as e: print(f'DEBUG: Movies fix failed: {e}')

    # 3. Ensure other tables exist
    tables = {
        'ml_models': 'model_id INT AUTO_INCREMENT PRIMARY KEY, model_name VARCHAR(255), model_type VARCHAR(100), algorithm VARCHAR(100), accuracy FLOAT, weight FLOAT, is_active BOOLEAN, trained_on DATETIME, version INT',
        'ml_models_rating': 'rating_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, movie_id BIGINT, score INT, review TEXT, is_recommended BOOLEAN, created_at DATETIME, updated_at DATETIME, UNIQUE KEY user_movie (user_id, movie_id)',
        'ml_models_person': 'person_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(200), role VARCHAR(20), photo VARCHAR(255), photo_url_external VARCHAR(2000)',
        'ml_models_moviecast': 'id INT AUTO_INCREMENT PRIMARY KEY, movie_id BIGINT, person_id INT, character_name VARCHAR(200), UNIQUE KEY movie_person (movie_id, person_id)',
        'dashboard_viewinghistory': 'history_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, movie_id BIGINT, watched_at DATETIME, time_spent_seconds INT, trailer_watch_seconds INT, click_count INT, progress FLOAT',
        'dashboard_watchlist': 'wishlist_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, movie_id BIGINT, added_at DATETIME',
        'dashboard_searchhistory': 'search_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, query VARCHAR(255), searched_at DATETIME',
        'users_user': 'user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(150) UNIQUE, email VARCHAR(255) UNIQUE, password VARCHAR(255), age INT, gender VARCHAR(10), profile_pic VARCHAR(255), bio TEXT, date_of_birth DATE, is_active BOOLEAN DEFAULT 1, is_admin BOOLEAN DEFAULT 0, admin_permissions VARCHAR(500), is_verified BOOLEAN DEFAULT 0, verification_token VARCHAR(100), duration_preference VARCHAR(20), language_preference VARCHAR(255), two_fa_code VARCHAR(10), reset_code VARCHAR(10), password_last_updated DATETIME, adult_content_filter BOOLEAN DEFAULT 0, otp_created_at DATETIME, created_at DATETIME',
        'users_genrepreference': 'pref_id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT, genre_id INT, preference_score FLOAT, created_at DATETIME'
    }
    for table_name, schema in tables.items():
        try:
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({schema})')
            print(f'DEBUG: Checked table {table_name}')
        except Exception as e: print(f'DEBUG: Table {table_name} error: {e}')

    # 4. Create Superusers
    try:
        from django.contrib.auth.models import User as AuthUser
        if not AuthUser.objects.filter(username='admin').exists():
            AuthUser.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print('Repair: Created superuser admin/admin123')
        
        from users.models import User as CustomUser
        from django.contrib.auth.hashers import make_password
        if not CustomUser.objects.filter(username='admin_viva').exists():
            CustomUser.objects.create(username='admin_viva', email='admin@viva.com', password=make_password('viva123'), age=25, gender='Male', is_active=True, is_admin=True, is_verified=True, admin_permissions='all')
            print('Repair: Created custom user admin_viva/viva123')
    except Exception as e: print(f'DEBUG: User creation error: {e}')
"

echo "--- Running remaining migrations ---"
python manage.py migrate --noinput

# Load data from backup if it exists
if [ -f "full_database_backup.json" ]; then
    echo "--- Loading Data from Backup ---"
    python manage.py loaddata full_database_backup.json || echo "Warning: loaddata failed, but continuing..."
fi

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
