from django.core.management.base import BaseCommand
from ml_models.models import Movies
from ml_models.visual_engine import VisualFeatureExtractor
from django.db.models import Q

class Command(BaseCommand):
    help = 'Reprocesses all movie posters to extract refined visual features (Palettes, Vibe, Complexity)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force re-processing of all movies')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of movies to process')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting visual feature refinement...'))

        extractor = VisualFeatureExtractor()

        movies_qs = Movies.objects.filter(
            Q(poster_url_external__isnull=False) | Q(poster__isnull=False)
        ).exclude(poster_url_external="")

        if options['limit']:
            movies_qs = movies_qs[:options['limit']]

        count = extractor.batched_extract(movies_qs, force=options['force'])

        self.stdout.write(self.style.SUCCESS(f'Successfully refined visual features for {count} movies.'))