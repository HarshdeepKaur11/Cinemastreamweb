import random
from django.core.management.base import BaseCommand
from ml_models.models import Movies, MovieStats

class Command(BaseCommand):
    help = 'Populates the MovieStats table with realistic, permanent ratings for all movies.'

    def handle(self, *args, **options):
        real_ratings = {
            'Toy Story': 4.1,
            'Waiting to Exhale': 3.0,
            'Father of the Bride Part II': 3.1,
            'Heat': 4.1,
            'Tom and Huck': 2.8,
            'The American President': 3.4,
            'Dracula: Dead and Loving It': 2.9,
            'Balto': 3.5,
            'Nixon': 3.5,
            'Cutthroat Island': 2.8,
            'GoldenEye': 3.6,
            'The American President': 3.4,
            'Sabrina': 3.2,
            'Babe': 3.5,
            'Casino': 4.1,
            'Sense and Sensibility': 3.8,
            'Four Rooms': 3.3,
            'Ace Ventura: When Nature Calls': 3.1,
            'Money Train': 2.8,
            'Get Shorty': 3.4,
            'Copycat': 3.3,
            'Assassins': 3.1,
            'Powder': 3.3,
            'Leaving Las Vegas': 3.8,
            'Othello': 3.6,
            'Now and Then': 3.4,
            'Persuasion': 3.8,
            'The City of Lost Children': 3.8,
            'Shanghai Triad': 3.6,
            'Dangerous Minds': 3.3,
            'Twelve Monkeys': 4.0,
            'Babe': 3.5,
            'Carrington': 3.5,
            'Dead Man Walking': 3.8,
            'Across the Sea of Time': 3.5,
            'It Takes Two': 3.1,
            'Clueless': 3.4,
            'Cry, the Beloved Country': 3.5,
            'Richard III': 3.7,
            'Dead Presidents': 3.3,
            'Restoration': 3.4,
            'Mortal Kombat': 2.9,
            'To Die For': 3.4,
            'How to Make an American Quilt': 3.1,
            'Seven': 4.3,
            'Pocahontas': 3.3,
            'When Night Is Falling': 3.5,
            'Usual Suspects, The': 4.3,
            'Guardians of the Galaxy': 4.0,
            'Interstellar': 4.4,
            'The Dark Knight': 4.5,
            'Animal': 3.2,
            'Maurh': 3.9,
            'Subedaar': 3.8,
            'Bambukat': 4.0,
            'Saiyaara': 3.5,
            'Jodi': 3.9,
            'Angrej': 4.1,
            'Ardaas Karaan': 4.2
        }

        movies = Movies.objects.all()
        count = 0

        for movie in movies:
            stats, created = MovieStats.objects.get_or_create(movie=movie)

            found_rating = None
            for title, rating in real_ratings.items():
                if title.lower() == movie.title.lower().strip():
                    found_rating = rating
                    break

            if found_rating:
                stats.avg_rating = found_rating
                stats.baseline_rating = found_rating
            else:
                random.seed(movie.movie_id)
                val = round(random.uniform(2.5, 4.3), 1)
                stats.avg_rating = val
                stats.baseline_rating = val

            stats.baseline_weight = 15

            random.seed(movie.movie_id + 500)
            stats.total_views = random.randint(500, 50000)
            stats.wishlist_count = random.randint(10, 2000)

            stats.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated ratings for {count} movies.'))