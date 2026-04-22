import random
from django.core.management.base import BaseCommand
from users.models import User
from ml_models.models import Movies, Rating, Genre
from dashboard.models import ViewingHistory
from django.utils import timezone

class Command(BaseCommand):
    help = 'Demonstrates the Soulmate Collaborative Filtering logic'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Setting up Soulmate Scenario..."))

        inception = Movies.objects.filter(title__icontains='Inception').first()
        interstellar = Movies.objects.filter(title__icontains='Interstellar').first()

        if not inception or not interstellar:
            all_m = list(Movies.objects.all()[:2])
            if len(all_m) < 2:
                self.stdout.write(self.style.ERROR("Not enough movies in DB to test."))
                return
            inception, interstellar = all_m

        user_a, _ = User.objects.get_or_create(
            username='user_a_presentation',
            defaults={'email': 'user_a@test.com', 'age': 25, 'is_active': True}
        )
        user_b, _ = User.objects.get_or_create(
            username='user_b_presentation',
            defaults={'email': 'user_b@test.com', 'age': 25, 'is_active': True}
        )

        ViewingHistory.objects.filter(user__in=[user_a, user_b]).delete()

        ViewingHistory.objects.create(user=user_a, movie=inception, progress=100, watched_at=timezone.now())
        ViewingHistory.objects.create(user=user_b, movie=inception, progress=100, watched_at=timezone.now())

        self.stdout.write(self.style.SUCCESS(f"User A and User B both watched '{inception.title}' (100%) -> They are now SOULMATES."))

        ViewingHistory.objects.create(user=user_a, movie=interstellar, progress=85, watched_at=timezone.now())

        self.stdout.write(self.style.SUCCESS(f"User A watched '{interstellar.title}' (85%)."))
        self.stdout.write(self.style.NOTICE(f"RESULT: User B should now see '{interstellar.title}' in their 'Collaborative Filtering' section because it's > 60%."))

        self.stdout.write(self.style.SUCCESS("\nScenario ready! Log in as 'user_b_presentation' (or search for them in Admin) to verify."))