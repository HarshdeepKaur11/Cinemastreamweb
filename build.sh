#!/usr/bin/env bash
python -m pip install --upgrade pip
pip install -r requirements.txt

# ONLY run collectstatic during build. 
# Do NOT run migrate here because the database might not be ready, 
# and SQLite migrations are failing due to a foreign key mismatch.
python manage.py collectstatic --noinput
