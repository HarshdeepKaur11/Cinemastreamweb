from django.db import models, transaction
from django.db.models import Avg
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os
from typing import TYPE_CHECKING

class Movies(models.Model):
    if TYPE_CHECKING:
        movie_genres: models.QuerySet['MovieGenre']
        movie_casts: models.QuerySet['MovieCast']
        match_percentage: int
        match_percentage_raw: float

    movie_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    release_year = models.IntegerField()
    language = models.CharField(max_length=100)
    duration = models.IntegerField(db_column='duration_minutes', null=True, blank=True)
    poster = models.ImageField(upload_to='posters/', null=True, blank=True)
    backdrop = models.ImageField(upload_to='backdrops/', null=True, blank=True)
    poster_url_external = models.URLField(max_length=2000, null=True, blank=True)
    backdrop_url_external = models.URLField(max_length=2000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    trailer_url = models.URLField(max_length=200, null=True, blank=True)
    content_rating = models.CharField(max_length=20, null=True, blank=True)
    content_descriptor = models.TextField(null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    dominant_color = models.CharField(max_length=50, null=True, blank=True, help_text="Hex code or color name (e.g., #FFFFFF)")

    class Meta:
        db_table = 'ml_models_movies'

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        if self.poster_url_external and self.poster_url_external.strip() and self.poster_url_external.lower() != 'nan':
            return self.poster_url_external
        p_name = getattr(self.poster, 'name', None)
        if self.poster and p_name and len(p_name) > 4 and p_name.lower() != 'nan':
            return self.poster.url
        return "https://placehold.co/400x600?text=No+Poster"

    @property
    def backdrop_url(self):
        if self.backdrop_url_external and self.backdrop_url_external.strip() and self.backdrop_url_external.lower() != 'nan':
            return self.backdrop_url_external
        b_name = getattr(self.backdrop, 'name', None)
        if self.backdrop and b_name and len(b_name) > 4 and b_name.lower() != 'nan':
            return self.backdrop.url
        return self.poster_url

    @property
    def duration_formatted(self):
        if not self.duration: return "0 min"
        hours = self.duration // 60
        mins = self.duration % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    def get_clean_genres(self):

        noise = [
            'english', 'hindi', 'punjabi', 'spanish', 'french', 'japanese', 'korean',
            'new release', 'uncategorized', 'unknown', 'ai specials'
        ]
        all_gs = [mg.genre.genre_name for mg in self.movie_genres.all()]
        return [g for g in all_gs if g.lower().strip() not in noise]

    def get_primary_genre(self):
        clean_gs = self.get_clean_genres()
        if clean_gs:
            return clean_gs[0]

        all_gs = [mg.genre.genre_name for mg in self.movie_genres.all()]
        if all_gs:
            return all_gs[0]

        return "Uncategorized"

    def get_genres_display(self, limit=None):
        clean_gs = self.get_clean_genres()
        if limit:
            clean_gs = clean_gs[:limit]

        return ", ".join(clean_gs) if clean_gs else "Uncategorized"

class Genre(models.Model):
    genre_id = models.AutoField(primary_key=True)
    genre_name = models.CharField(max_length=100, db_column='name')

    class Meta:
        db_table = 'ml_models_genre'

    def __str__(self):
        return self.genre_name

class MovieGenre(models.Model):
    if TYPE_CHECKING:
        movie_id: int
        genre_id: int

    movie = models.ForeignKey('Movies', on_delete=models.CASCADE, related_name='movie_genres')
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE, related_name='movie_genres')

    class Meta:
        db_table = 'ml_models_moviegenre'

    def __str__(self):
        return f"{self.movie.title} - {self.genre.genre_name}"

class Person(models.Model):
    person_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    ROLE_CHOICES = [
        ('actor', 'Actor'),
        ('director', 'Director'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    photo = models.ImageField(upload_to='persons/', null=True, blank=True)
    photo_url_external = models.URLField(max_length=2000, null=True, blank=True)

    @property
    def photo_url(self):
        if self.photo_url_external:
            return self.photo_url_external
        ph_name = getattr(self.photo, 'name', None)
        if self.photo and ph_name and len(ph_name) > 4 and ph_name.lower() != 'nan':
            return self.photo.url
        return f"https://ui-avatars.com/api/?name={self.name.replace(' ', '+')}"

    class Meta:
        db_table = 'ml_models_person'

    def __str__(self):
        return f"{self.name} ({self.role})"

@receiver(post_save, sender='ml_models.Rating')
@receiver(models.signals.post_delete, sender='ml_models.Rating')
def update_movie_stats_on_rating(sender, instance, **kwargs):

    stats, created = MovieStats.objects.get_or_create(movie=instance.movie)
    stats.update_rating()

class MovieCast(models.Model):
    if TYPE_CHECKING:
        movie_id: int
        person_id: int

    movie = models.ForeignKey('Movies', on_delete=models.CASCADE, related_name='movie_casts')
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name='movie_casts')
    character_name = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ('movie', 'person')
        db_table = 'ml_models_moviecast'

    def __str__(self):
        return f"{self.person.name} in {self.movie.title}"

class MovieStats(models.Model):
    if TYPE_CHECKING:
        movie_id: int

    stat_id = models.AutoField(primary_key=True)
    movie = models.OneToOneField('Movies', on_delete=models.CASCADE, related_name='stats')
    total_views = models.PositiveIntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    baseline_rating = models.FloatField(default=3.5, help_text="Initial 'Real Life' rating (IMDb-like)")
    baseline_weight = models.PositiveIntegerField(default=15, help_text="Weight of the baseline rating (virtual votes)")
    avg_completion = models.FloatField(default=0.0)
    total_watch_seconds = models.BigIntegerField(default=0)
    wishlist_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movie_stats'

    def __str__(self):
        return f"Stats for {self.movie.title}"

    def update_rating(self):

        user_ratings_qs = Rating.objects.filter(movie=self.movie).exclude(score__isnull=True)
        user_count = user_ratings_qs.count()
        user_sum = user_ratings_qs.aggregate(models.Sum('score'))['score__sum'] or 0

        weighted_sum = (self.baseline_rating * self.baseline_weight) + user_sum
        total_weight = self.baseline_weight + user_count

        new_avg = weighted_sum / total_weight if total_weight > 0 else self.baseline_rating
        self.avg_rating = round(new_avg, 1)
        self.save()

@receiver(post_save, sender=Movies)
def create_movie_stats(sender, instance, created, **kwargs):
    if created:
        MovieStats.objects.get_or_create(movie=instance)

class Rating(models.Model):
    movie_id: int
    user_id: int

    rating_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    movie = models.ForeignKey('Movies', on_delete=models.CASCADE)
    score = models.IntegerField(null=True, blank=True)
    review = models.TextField(blank=True)
    is_recommended = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ml_models_rating'
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.score} stars"

@receiver(post_save, sender=Rating)
def auto_train_on_feedback(sender, instance, created, **kwargs):

    if not created: return

    from django.core.management import call_command
    import threading

    last_train_entry = MLModels.objects.filter(model_name='Hybrid Recommendation Model').first()
    if not last_train_entry or not last_train_entry.trained_on:
        return

    new_ratings_count = Rating.objects.filter(created_at__gt=last_train_entry.trained_on).count()

    if new_ratings_count >= 10:
        def run_auto_train():
            try:

                call_command('train_models')
                print(f"AUTO-LEARNING TRIGGERED SUCCESSFULLY. System has learned from {new_ratings_count} new ratings.")
            except Exception as e:
                print(f"AUTO-LEARNING FAILED: {str(e)}")

        from django.db import transaction
        transaction.on_commit(lambda: threading.Thread(target=run_auto_train).start())

class MLModels(models.Model):
    model_id = models.AutoField(primary_key=True)
    model_name = models.CharField(max_length=255)
    model_type = models.CharField(max_length=100)
    algorithm = models.CharField(max_length=100)
    accuracy = models.FloatField()
    weight = models.FloatField(default=0.5)
    is_active = models.BooleanField(default=True)
    trained_on = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(default=1)

    class Meta:
        db_table = 'ml_models'

    def __str__(self):
        return self.model_name

class PosterColorProfile(models.Model):
    profile_id = models.BigAutoField(primary_key=True)
    movie = models.OneToOneField('Movies', on_delete=models.CASCADE, related_name='color_profile')
    theme = models.CharField(max_length=50, null=True, blank=True)
    dominant_hex = models.CharField(max_length=10, null=True, blank=True)
    palette_json = models.TextField(null=True, blank=True)
    brightness = models.FloatField(default=0.0)
    saturation = models.FloatField(default=0.0)
    analyzed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ml_models_postercolorprofile'

    def __str__(self):
        return f"Color Palette for {self.movie.title}"

@receiver(post_delete, sender=Movies)
def delete_movie_media(sender, instance, **kwargs):
    """Deletes poster and backdrop files from filesystem when Movie is deleted."""
    if instance.poster:
        if os.path.isfile(instance.poster.path):
            try:
                os.remove(instance.poster.path)
            except Exception:
                pass
    if instance.backdrop:
        if os.path.isfile(instance.backdrop.path):
            try:
                os.remove(instance.backdrop.path)
            except Exception:
                pass

@receiver(post_delete, sender=Person)
def delete_person_media(sender, instance, **kwargs):
    """Deletes photo file from filesystem when Person is deleted."""
    if instance.photo:
        if os.path.isfile(instance.photo.path):
            try:
                os.remove(instance.photo.path)
            except Exception:
                pass