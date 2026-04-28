#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "--- Python Version ---"
python --version

echo "--- Installing Pip ---"
python -m pip install --upgrade pip

echo "--- Installing Requirements ---"
pip install -r requirements.txt

echo "--- Running Collectstatic ---"
# We use --clear to ensure no stale files, and continue even if it warns
python manage.py collectstatic --noinput --clear

echo "--- Build Complete ---"
