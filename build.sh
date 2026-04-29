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

    # 3. Fix ml_models table (and potentially create it)
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS ml_models (model_id INT AUTO_INCREMENT PRIMARY KEY, model_name VARCHAR(255), model_type VARCHAR(100), algorithm VARCHAR(100), accuracy FLOAT, weight FLOAT, is_active BOOLEAN, trained_on DATETIME, version INT)')
    except Exception as e: print(f'ML table error: {e}')

    # 4. Fix Dashboard tables (ViewingHistory, Watchlist, SearchHistory)
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS dashboard_viewinghistory (history_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, movie_id BIGINT, watched_at DATETIME, time_spent_seconds INT, trailer_watch_seconds INT, click_count INT, progress FLOAT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS dashboard_watchlist (wishlist_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, movie_id BIGINT, added_at DATETIME)')
        cursor.execute('CREATE TABLE IF NOT EXISTS dashboard_searchhistory (search_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, query VARCHAR(255), searched_at DATETIME)')
        print('Repair: Ensured dashboard tables exist.')
    except Exception as e: print(f'Dashboard table error: {e}')

    # 5. Fix Users table
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS users_user (user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(150) UNIQUE, email VARCHAR(255) UNIQUE, password VARCHAR(255), age INT, gender VARCHAR(10), profile_pic VARCHAR(255), bio TEXT, date_of_birth DATE, is_active BOOLEAN DEFAULT 1, is_admin BOOLEAN DEFAULT 0, admin_permissions VARCHAR(500), is_verified BOOLEAN DEFAULT 0, verification_token VARCHAR(100), duration_preference VARCHAR(20), language_preference VARCHAR(255), two_fa_code VARCHAR(10), reset_code VARCHAR(10), password_last_updated DATETIME, adult_content_filter BOOLEAN DEFAULT 0, otp_created_at DATETIME, created_at DATETIME)')
        cursor.execute('CREATE TABLE IF NOT EXISTS users_genrepreference (pref_id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT, genre_id INT, preference_score FLOAT, created_at DATETIME)')
        print('Repair: Ensured users tables exist.')
    # 6. Create Superuser if not exists
    try:
        from django.contrib.auth.models import User as AuthUser
        if not AuthUser.objects.filter(username='admin').exists():
            AuthUser.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            print('Repair: Created superuser admin/admin123')
    # 7. Create Custom User in users_user if not exists
    try:
        from users.models import User as CustomUser
        from django.contrib.auth.hashers import make_password
        if not CustomUser.objects.filter(username='admin_viva').exists():
            CustomUser.objects.create(
                username='admin_viva',
                email='admin@viva.com',
                password=make_password('viva123'),
                age=25,
                gender='Male',
                is_active=True,
                is_admin=True,
                is_verified=True,
                admin_permissions='all'
            )
            print('Repair: Created custom user admin_viva/viva123')
    except Exception as e: print(f'Custom user error: {e}')
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
