

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.user_dashboard_view, name='user_dashboard_default'),
    path('user_dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('history/', views.history_view, name='history'),
    path('delete-from-watchlist/<int:movie_id>/', views.delete_from_watchlist_view, name='delete_from_watchlist'),
    path('delete-history/<int:history_id>/', views.delete_history_view, name='delete_history'),
    path('clear-history/', views.clear_all_history_view, name='clear_all_history'),
    path('moviedetails/<int:movie_id>/', views.moviedetails_view, name='moviedetails'),
    path('submit-review/<int:movie_id>/', views.submit_review_view, name='submit_review'),
    path('delete-review/<int:movie_id>/', views.delete_review_view, name='delete_review'),
    path('delete-all-reviews/', views.delete_all_reviews_view, name='delete_all_reviews'),
    path('add-to-watchlist/<int:movie_id>/', views.add_to_watchlist_view, name='add_to_watchlist'),
    path('mark-watched/<int:movie_id>/', views.mark_as_watched_view, name='mark_as_watched'),
    path('update-watch-time/<int:movie_id>/', views.update_watch_time_view, name='update_watch_time'),
]