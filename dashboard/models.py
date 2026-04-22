from django.db import models
from users.models import User
from typing import TYPE_CHECKING

class Watchlist(models.Model):
    if TYPE_CHECKING:
        movie_id: int
        user_id: int

    wishlist_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('ml_models.Movies', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        movie_title = getattr(self.movie, 'title', 'Unknown Movie')
        return f"{self.user.username}'s Watchlist - {movie_title}"

class ViewingHistory(models.Model):
    if TYPE_CHECKING:
        movie_id: int
        user_id: int

    history_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('ml_models.Movies', on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now=True)
    time_spent_seconds = models.IntegerField(default=0)
    trailer_watch_seconds = models.IntegerField(default=0)
    click_count = models.IntegerField(default=1)
    progress = models.FloatField(default=0.0)

    def __str__(self):
        movie_title = getattr(self.movie, 'title', 'Unknown Movie')
        return f"{self.user.username} - {movie_title} ({self.progress}%)"

class SearchHistory(models.Model):
    if TYPE_CHECKING:
        user_id: int | None

    search_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dashboard_searchhistory'

    def __str__(self):
        return f"{self.user.username if self.user else 'Guest'} - {self.query}"