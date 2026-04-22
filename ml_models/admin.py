from django.contrib import admin
from .models import Movies, Genre, MovieGenre, PosterColorProfile

@admin.register(PosterColorProfile)
class PosterColorProfileAdmin(admin.ModelAdmin):
    list_display = ('movie', 'theme', 'dominant_hex', 'brightness', 'analyzed_at')
    search_fields = ('movie__title', 'theme', 'dominant_hex')

class MovieGenreInline(admin.TabularInline):
    model = MovieGenre
    extra = 1

@admin.register(Movies)
class MoviesAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year', 'get_avg_rating', 'language')

    @admin.display(description='Avg Rating')
    def get_avg_rating(self, obj):
        return obj.stats.avg_rating if hasattr(obj, 'stats') else 0.0
    list_filter = ('release_year', 'language')
    search_fields = ('title', 'movie_id')
    ordering = ('title',)
    inlines = [MovieGenreInline]

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('genre_name',)
    search_fields = ('genre_name',)

@admin.register(MovieGenre)
class MovieGenreAdmin(admin.ModelAdmin):
    list_display = ('movie', 'genre')
    list_filter = ('genre',)
    search_fields = ('movie__title', 'genre__genre_name')