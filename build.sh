#!/usr/bin/env bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed"
# Migrations will be handled in the Procfile or manually
