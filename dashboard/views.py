from django.shortcuts import redirect, render, get_object_or_404
from typing import Any
from django.http import JsonResponse
from dashboard.models import Watchlist, ViewingHistory, SearchHistory
from users.models import User
from users.decorators import login_required_custom
from django.contrib import messages
from django.db import models, transaction
from ml_models.models import Movies, Rating, MovieStats, Genre
from django.core.cache import cache
from django.db.models import Q, Count
import random
import logging

logger = logging.getLogger(__name__)

@login_required_custom
def user_dashboard_view(request):
    user = request.current_user

    cache_key = f"user_dash_v16_{user.user_id}"
    cached_response_context = cache.get(cache_key)

    if cached_response_context:
        return render(request, 'dashboard/user_dashboard.html', cached_response_context)

    from ml_models.utils import get_smart_recommendations, get_safety_filter, apply_match_scores

    poster_filter = Q(poster_url_external__isnull=False) & ~Q(poster_url_external="") & ~Q(poster_url_external__icontains="nan")

    safety_filter = get_safety_filter()

    use_safety = getattr(user, 'adult_content_filter', True) or (user.age is not None and user.age < 18)

    user_wishlist_qs = Watchlist.objects.filter(user=user).filter(movie__poster_url_external__isnull=False).select_related('movie')
    if use_safety:
        user_wishlist_qs = user_wishlist_qs.exclude(movie__in=Movies.objects.filter(safety_filter))
        user_wishlist_qs = user_wishlist_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Romance')
        user_wishlist_qs = user_wishlist_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Erotica')
        user_wishlist_qs = user_wishlist_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Adult')
    user_wishlist = list(user_wishlist_qs[:20])
    wishlist_movies = [item.movie for item in user_wishlist]
    if wishlist_movies:
        wishlist_movies = apply_match_scores(user, wishlist_movies, source='profile')

    full_history_qs = ViewingHistory.objects.filter(user=user).select_related('movie').order_by('-watched_at')
    if use_safety:
        full_history_qs = full_history_qs.exclude(movie__in=Movies.objects.filter(safety_filter))
        full_history_qs = full_history_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Romance')
        full_history_qs = full_history_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Erotica')
        full_history_qs = full_history_qs.exclude(movie__movie_genres__genre__genre_name__icontains='Adult')

    continue_watching_list = list(full_history_qs.filter(progress__lt=95, progress__gt=5)[:15])
    continue_movies = [record.movie for record in continue_watching_list]
    if continue_movies:
        continue_movies = apply_match_scores(user, continue_movies, source='history')

    smart_recs = get_smart_recommendations(user)

    from users.models import GenrePreference
    user_pref_ids = set(GenrePreference.objects.filter(user=user).values_list('genre_id', flat=True))

    all_genres = list(Genre.objects.annotate(m_c=Count('movie_genres')).filter(m_c__gt=5).exclude(
        genre_name__in=['English', 'Hindi', 'Punjabi', 'Spanish', 'Japanese', 'Korean', 'French']
    ).order_by('-m_c')[:12])

    selectable_exclude_list = [
        'English', 'Hindi', 'Punjabi', 'Spanish', 'French', 'Japanese', 'Korean',
        'Musical', 'New Release', 'AI Specials'
    ]
    selectable_genre_ids = set(Genre.objects.exclude(genre_name__in=selectable_exclude_list).values_list('genre_id', flat=True))

    genre_sections_data: list[dict[str, Any]] = []

    for g in all_genres:

        g_name_lower = g.genre_name.lower()
        if use_safety and any(x in g_name_lower for x in ['romance', 'erotica', 'adult']):
            continue

        if user_pref_ids and g.genre_id not in user_pref_ids:
            continue

        movies_qs = Movies.objects.filter(movie_genres__genre=g).filter(poster_filter).select_related('stats')
        if use_safety:
            movies_qs = movies_qs.exclude(safety_filter)

        movies = list(movies_qs.distinct()[:15])

        if g_name_lower == 'crime' and user.age is not None and user.age < 16:
            continue

        if movies:
            scored = apply_match_scores(user, movies, source='profile')
            genre_sections_data.append({
                'genre_name': g.genre_name,
                'genre_id': g.genre_id,
                'movies': sorted(scored, key=lambda x: getattr(x, 'match_percentage_raw', 0), reverse=True)
            })

    if not use_safety:
        romance_g = Genre.objects.filter(Q(genre_name__icontains='Romance') | Q(genre_name__icontains='Erotica')).first()
        if romance_g:

            if not user_pref_ids or romance_g.genre_id in user_pref_ids:
                if not any(d['genre_id'] == romance_g.genre_id for d in genre_sections_data):
                    r_movies_qs = Movies.objects.filter(movie_genres__genre=romance_g).filter(poster_filter).distinct()[:15]
                    r_movies = list(r_movies_qs)
                    if r_movies:
                        r_scored = apply_match_scores(user, r_movies, source='profile')
                        genre_sections_data.append({
                            'genre_name': 'Romance & Love',
                            'genre_id': romance_g.genre_id,
                            'movies': sorted(r_scored, key=lambda x: getattr(x, 'match_percentage_raw', 0), reverse=True)
                        })

    def get_movies_by_language(lang_list):
        from ml_models.utils import get_safety_filter

        poster_filter = Q(poster_url_external__isnull=False) & ~Q(poster_url_external="") & ~Q(poster_url_external__icontains="nan")
        qs = Movies.objects.filter(language__in=lang_list).filter(poster_filter).select_related('stats')

        if user_pref_ids:
            qs = qs.filter(movie_genres__genre__genre_id__in=user_pref_ids)

        if use_safety:
            qs = qs.exclude(safety_filter)
        movies = list(qs.distinct()[:15])
        return apply_match_scores(user, movies, source='profile')

    hybrid_list = list(smart_recs.get('hybrid', []))
    lang_pref_raw = getattr(user, 'language_preference', 'English') or 'English'
    lang_prefs = [lp.strip().lower() for lp in lang_pref_raw.split(',') if lp.strip()]

    top_candidates_pool = hybrid_list[:150]
    lang_buckets = {lp: [] for lp in lang_prefs}
    lang_buckets['other'] = []

    for m in top_candidates_pool:
        m_lang = (getattr(m, 'language', '') or '').lower()
        matched = False
        for lp in lang_prefs:
            if lp in m_lang:
                lang_buckets[lp].append(m)
                matched = True
                break
        if not matched:
            lang_buckets['other'].append(m)

    interleaved_hero = []
    max_hero_size = 15
    for i in range(max_hero_size):
        for lp in lang_prefs:
            if i < len(lang_buckets[lp]):
                item = lang_buckets[lp][i]
                if item not in interleaved_hero:
                    interleaved_hero.append(item)
            if len(interleaved_hero) >= max_hero_size: break

        if len(interleaved_hero) < max_hero_size and i < len(lang_buckets['other']):
            item = lang_buckets['other'][i]
            if item not in interleaved_hero:
                interleaved_hero.append(item)

        if len(interleaved_hero) >= max_hero_size: break

    trending_movies = interleaved_hero

    all_context_movies = []
    if trending_movies: all_context_movies.extend(trending_movies)
    all_context_movies.extend(wishlist_movies)
    all_context_movies.extend(continue_movies)
    all_context_movies.extend(smart_recs.get('history_based', []))
    for g_section in genre_sections_data: all_context_movies.extend(g_section['movies'])

    for m in all_context_movies:
        if not hasattr(m, 'stats') or not m.stats:
            from ml_models.models import MovieStats
            m.stats, _ = MovieStats.objects.get_or_create(movie=m)

    user_id = user.user_id
    full_history_qs = ViewingHistory.objects.filter(user=user).select_related('movie').order_by('-watched_at')

    user_ratings = Rating.objects.filter(user=user).select_related('movie')
    rating_map = {r.movie.movie_id: r for r in user_ratings}

    def attach_rating_metadata(movie_list):
        if not movie_list: return
        for m in movie_list:
            if m.movie_id in rating_map:
                r = rating_map[m.movie_id]
                m.my_rating = r.score
                m.is_recommended = r.is_recommended
            else:
                m.my_rating = 0
                m.is_recommended = None

    attach_rating_metadata(trending_movies)
    attach_rating_metadata(wishlist_movies)
    attach_rating_metadata(continue_watching_list)

    attach_rating_metadata(smart_recs.get('hybrid'))
    attach_rating_metadata(smart_recs.get('collaborative_based'))
    attach_rating_metadata(smart_recs.get('true_collaborative'))
    attach_rating_metadata(smart_recs.get('visual_content'))
    attach_rating_metadata(smart_recs.get('poster_based'))
    attach_rating_metadata(smart_recs.get('chromatic_harmony'))
    attach_rating_metadata(smart_recs.get('duration_based'))
    attach_rating_metadata(smart_recs.get('rating_based'))
    attach_rating_metadata(smart_recs.get('history_based'))
    attach_rating_metadata(smart_recs.get('cold_start'))

    for g_section in genre_sections_data:
        attach_rating_metadata(g_section['movies'])

    def fetch_lang_movies(lang_name):
        qs = Movies.objects.filter(language__icontains=lang_name).filter(Q(poster_url_external__isnull=False) & ~Q(poster_url_external="") & ~Q(poster_url_external__icontains="nan")).select_related('stats')

        if user_pref_ids:
            qs = qs.filter(movie_genres__genre__genre_id__in=user_pref_ids)

        if use_safety:
            qs = qs.exclude(safety_filter)
            qs = qs.exclude(movie_genres__genre__genre_name__icontains='Romance')
            qs = qs.exclude(movie_genres__genre__genre_name__icontains='Erotica')
            qs = qs.exclude(movie_genres__genre__genre_name__icontains='Adult')

        if user.age is not None and user.age < 16:
            qs = qs.exclude(movie_genres__genre__genre_name__icontains='Crime')

        lang_movies = list(qs.distinct()[:20])

        if len(lang_movies) < 5 and user_pref_ids:
            fallback_qs = Movies.objects.filter(language__icontains=lang_name).filter(poster_filter).select_related('stats')
            if use_safety: fallback_qs = fallback_qs.exclude(safety_filter)
            if user.age is not None and user.age < 16: fallback_qs = fallback_qs.exclude(movie_genres__genre__genre_name__icontains='Crime')

            fallback_qs = fallback_qs.exclude(movie_id__in=[m.movie_id for m in lang_movies])
            lang_movies.extend(list(fallback_qs.distinct()[:15 - len(lang_movies)]))

        return apply_match_scores(user, lang_movies, source='profile')

    punjabi_movies = fetch_lang_movies('Punjabi')
    hindi_movies = fetch_lang_movies('Hindi')
    korean_movies = fetch_lang_movies('Korean')
    japanese_movies = fetch_lang_movies('Japanese')

    attach_rating_metadata(punjabi_movies)
    attach_rating_metadata(hindi_movies)
    attach_rating_metadata(korean_movies)
    attach_rating_metadata(japanese_movies)

    watched_30_percent = full_history_qs.filter(progress__gte=30).count()
    user_engaged_enough = watched_30_percent >= 1

    history_records = list(full_history_qs[:30])
    scored_history_movies = apply_match_scores(user, [r.movie for r in history_records], source='history')
    for i, r in enumerate(history_records):
        r.movie = scored_history_movies[i]

    context = {
        'current_user': user,
        'wishlist': user_wishlist,
        'continue_watching': list(continue_watching_list),
        'full_history': history_records,
        'trending_movies': list(trending_movies),
        'hybrid_movies': list(smart_recs.get('hybrid', [])),
        'collaborative_movies': list(smart_recs.get('collaborative_based', [])),
        'true_collab_movies': list(smart_recs.get('true_collaborative', [])),
        'visual_content_movies': list(smart_recs.get('visual_content', [])),
        'poster_based_movies': list(smart_recs.get('poster_based', [])),
        'chromatic_harmony_movies': list(smart_recs.get('chromatic_harmony', [])),
        'punjabi_movies': punjabi_movies,
        'hindi_movies': hindi_movies,
        'korean_movies': korean_movies,
        'japanese_movies': japanese_movies,
        'visual_theme_name': smart_recs.get('visual_theme_name'),
        'duration_based_movies': list(smart_recs.get('duration_based', [])),
        'rating_based_movies': list(smart_recs.get('rating_based', [])),
        'history_based_movies': list(smart_recs.get('history_based', [])),
        'cold_start_movies': list(smart_recs.get('cold_start', [])),
        'all_genres_list': all_genres,
        'genre_sections_data': genre_sections_data,
        'global_movies': get_movies_by_language(['Japanese', 'Korean', 'Spanish', 'French']),
        'user_has_history': smart_recs.get('user_has_history', False),
        'user_engaged_enough': user_engaged_enough,
        'watched_30_percent': watched_30_percent,
        'history_count': full_history_qs.count(),
        'watched_60_percent': full_history_qs.filter(progress__gte=60).count(),
        'has_ratings': Rating.objects.filter(user=user).exists(),
    }

    cache_key = f"user_dash_v16_{user.user_id}"
    cache.set(cache_key, context, 3600)
    return render(request, 'dashboard/user_dashboard.html', context)

@login_required_custom
def history_view(request):
    current_user = request.current_user
    full_history = ViewingHistory.objects.filter(user=current_user).order_by('-watched_at')
    return render(request, 'dashboard/history.html', {'history': full_history, 'current_user': current_user})

def moviedetails_view(request, movie_id):
    movie = get_object_or_404(Movies, movie_id=movie_id)
    from ml_models.utils import get_safety_filter
    safety_filter = get_safety_filter()
    u_id = request.session.get('user_id')
    user_obj = User.objects.filter(user_id=u_id).first() if u_id else None
    use_safety = getattr(user_obj, 'adult_content_filter', True) or (getattr(user_obj, 'age', 18) < 18)
    if Movies.objects.filter(pk=movie_id).filter(safety_filter).exists() and use_safety:
        messages.warning(request, "This content is restricted based on your maturity settings.")
        return redirect('dashboard:user_dashboard')
    from ml_models.utils import get_related_movies, apply_match_scores
    related_movies = get_related_movies(movie, user=user_obj)
    if user_obj:

        from django.utils import timezone
        ViewingHistory.objects.update_or_create(
            user=user_obj,
            movie=movie,
            defaults={'watched_at': timezone.now()}
        )

        from django.core.cache import cache
        cache.delete(f"user_dash_v16_{user_obj.user_id}")

    cast = movie.movie_casts.select_related('person').all()
    directors = [c.person.name for c in cast if c.person.role == 'director']
    starring = [c.person.name for c in cast if c.person.role == 'actor']

    return render(request, 'dashboard/moviedetails.html', {
        'movie': movie,
        'related_movies': related_movies,
        'current_user': user_obj,
        'cast': cast,
        'directors': directors,
        'starring': starring
    })

@login_required_custom
def add_to_watchlist_view(request, movie_id):
    movie = get_object_or_404(Movies, movie_id=movie_id)
    watchlist_item, created = Watchlist.objects.get_or_create(user=request.current_user, movie=movie)
    from django.core.cache import cache
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Added to your watchlist!'})

    return redirect('dashboard:user_dashboard')

@login_required_custom
def delete_from_watchlist_view(request, movie_id):
    movie = get_object_or_404(Movies, movie_id=movie_id)
    Watchlist.objects.filter(user=request.current_user, movie=movie).delete()
    from django.core.cache import cache
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")
    return redirect('dashboard:user_dashboard')

@login_required_custom
def delete_history_view(request, history_id):
    history = get_object_or_404(ViewingHistory, pk=history_id, user=request.current_user)
    history.delete()
    from django.core.cache import cache
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")
    return redirect('dashboard:user_dashboard')

@login_required_custom
def clear_all_history_view(request):
    ViewingHistory.objects.filter(user=request.current_user).delete()
    from django.core.cache import cache
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")
    return redirect('dashboard:history')

@login_required_custom
def submit_review_view(request, movie_id):
    if request.method == 'POST':
        score = request.POST.get('rating')
        review_text = request.POST.get('comment') or ""
        is_rec_str = request.POST.get('recommend')

        movie = get_object_or_404(Movies, movie_id=movie_id)

        defaults: dict[str, Any] = {}
        if score:
            defaults['score'] = int(score)
        if review_text is not None:
            defaults['review'] = review_text
        if is_rec_str:
            defaults['is_recommended'] = (is_rec_str == 'yes')

        if defaults:
            Rating.objects.update_or_create(
                user=request.current_user,
                movie=movie,
                defaults=defaults
            )
            from django.core.cache import cache
            cache.delete(f"user_dash_v16_{request.current_user.user_id}")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return redirect('dashboard:moviedetails', movie_id=movie_id)

@login_required_custom
def delete_review_view(request, movie_id):
    movie = get_object_or_404(Movies, movie_id=movie_id)

    Rating.objects.filter(user=request.current_user, movie=movie).delete()

    from ml_models.models import MovieStats
    stats, _ = MovieStats.objects.get_or_create(movie=movie)
    stats.update_rating()

    from django.core.cache import cache
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('users:profile')

@login_required_custom
def mark_as_watched_view(request, movie_id):
    movie = get_object_or_404(Movies, movie_id=movie_id)
    ViewingHistory.objects.update_or_create(user=request.current_user, movie=movie, defaults={'progress': 100})
    cache.delete(f"user_dash_v16_{request.current_user.user_id}")
    return redirect('dashboard:user_dashboard')

@login_required_custom
def update_watch_time_view(request, movie_id):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            is_ended = data.get('ended', False)

            movie = get_object_or_404(Movies, movie_id=movie_id)
            history, created = ViewingHistory.objects.get_or_create(user=request.current_user, movie=movie)

            if is_ended:
                history.progress = 100.0
            else:

                current_p = data.get('progress')
                if current_p is not None:
                    history.progress = float(current_p)
                elif history.progress < 90:

                    history.progress += 2.0

            history.save()

            if is_ended:
                 from django.core.cache import cache
                 cache.delete(f"user_dash_v16_{request.current_user.user_id}")

            return JsonResponse({'status': 'success', 'new_progress': history.progress})
        except Exception as e:
            logger.exception("Error updating watch time for movie %s and user %s", movie_id, request.current_user.user_id)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required_custom
def delete_all_reviews_view(request):
    user = request.current_user
    with transaction.atomic():
        deleted_count, _ = Rating.objects.filter(user=user).delete()

        cache_key = f"user_dash_v16_{user.user_id}"
        cache.delete(cache_key)

    if deleted_count > 0:
        messages.success(request, f"Successfully cleared all {deleted_count} ratings and reviews.")
    else:
        messages.info(request, "No ratings found to delete.")

    return redirect('users:profile')