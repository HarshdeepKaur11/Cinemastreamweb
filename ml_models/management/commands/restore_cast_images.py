import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from ml_models.models import Movies, Person, MovieCast

class Command(BaseCommand):
    help = 'Restores missing cast images with high reliability'

    def add_arguments(self, parser):
        parser.add_argument('--language', type=str)
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        api_key = getattr(settings, 'TMDB_API_KEY', None)
        session = requests.Session()

        lang = options.get('language')
        if lang:
            movies = Movies.objects.filter(language__icontains=lang)
        else:
            movies = Movies.objects.all()

        self.stdout.write(f"Processing {movies.count()} movies...")

        for movie in movies:
            self.stdout.write(f"\nTargeting: {movie.title} ({movie.language})")

            tmdb_id = None
            try:
                s_url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie.title}"
                s_resp = session.get(s_url, timeout=20)
                if s_resp.status_code == 200:
                    results = s_resp.json().get('results')
                    if results: tmdb_id = results[0]['id']
            except: pass

            if not tmdb_id: tmdb_id = movie.movie_id

            c_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits?api_key={api_key}"
            for attempt in range(3):
                try:
                    time.sleep(1.0)
                    c_resp = session.get(c_url, timeout=25)
                    if c_resp.status_code == 200:
                        data = c_resp.json()
                        cast = data.get('cast', [])[:10]
                        directors = [c for c in data.get('crew', []) if c.get('job') == 'Director']

                        for item in (cast + directors[:1]):
                            name = item.get('name')
                            profile = item.get('profile_path')
                            if not profile: continue

                            photo_url = f"https://image.tmdb.org/t/p/w200{profile}"
                            role = 'actor' if 'character' in item else 'director'

                            person, _ = Person.objects.get_or_create(name=name, role=role)
                            person.photo_url_external = photo_url
                            person.save()
                            MovieCast.objects.get_or_create(movie=movie, person=person)

                        self.stdout.write(self.style.SUCCESS(f"Restored: {movie.title}"))
                        break
                except Exception as e:
                    if attempt == 2:
                        self.stdout.write(self.style.ERROR(f"Failed {movie.title}: {e}"))
                    time.sleep(3)