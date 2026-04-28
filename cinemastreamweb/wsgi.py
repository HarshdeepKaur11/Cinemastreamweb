

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinemastreamweb.settings')

application = get_wsgi_application()

# --- AUTO-MIGRATE ON STARTUP ---
try:
    print("--- Checking for Database Migrations ---")
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    print("--- Database is Up to Date ---")
except Exception as e:
    print(f"--- Auto-Migration Error: {e} ---")