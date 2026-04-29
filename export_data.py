import os
import django
import json
from django.core.serializers import serialize

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinemastreamweb.settings')
django.setup()

from users.models import User, GenrePreference
from ml_models.models import Movies, Genre, MovieGenre, Person, MovieCast, MovieStats, Rating, MLModels, PosterColorProfile
from dashboard.models import Watchlist, ViewingHistory, SearchHistory
from core.models import ContactMessage

def export_all_data():
    print("--- Starting Full Data Export ---")
    
    models_to_export = [
        User, Genre, Movies, MovieGenre, Person, MovieCast, 
        MovieStats, Rating, MLModels, PosterColorProfile,
        Watchlist, ViewingHistory, SearchHistory, GenrePreference,
        ContactMessage
    ]
    
    all_objects = []
    
    for model in models_to_export:
        try:
            count = model.objects.count()
            print(f"Exporting {model.__name__}: {count} records...")
            data = serialize('json', model.objects.all())
            all_objects.extend(json.loads(data))
        except Exception as e:
            print(f"Error exporting {model.__name__}: {e}")

    output_file = 'full_database_backup.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_objects, f, indent=2)
    
    print(f"\n--- Export Complete! ---")
    print(f"Data saved to: {os.path.abspath(output_file)}")
    print("\nNext Steps:")
    print("1. Update your .env file with TiDB credentials.")
    print("2. Run: python manage.py migrate")
    print("3. Run: python manage.py loaddata full_database_backup.json")

if __name__ == "__main__":
    export_all_data()
