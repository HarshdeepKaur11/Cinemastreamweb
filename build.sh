#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Upgrading Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Core Packages ---"
pip install --no-cache-dir Django django-environ gunicorn whitenoise pillow requests python-dotenv

echo "--- Installing Heavy ML Packages (Sequential to save RAM) ---"
pip install --no-cache-dir numpy
pip install --no-cache-dir pandas
pip install --no-cache-dir scipy
pip install --no-cache-dir scikit-learn
pip install --no-cache-dir opencv-python-headless
pip install --no-cache-dir mysql-connector-python

echo "--- Running Collectstatic ---"
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed, but continuing..."

echo "--- Build Complete ---"
