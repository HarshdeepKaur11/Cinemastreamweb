#!/usr/bin/env bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput || echo "Collectstatic failed, but continuing..."
python manage.py migrate --noinput || echo "Migrate failed, but continuing..."
