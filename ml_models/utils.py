import os
import json
import joblib
import numpy as np
from django.conf import settings
from django.db.models import Count, Q, Case, When, Value, IntegerField
from .models import Movies, Rating, MovieGenre, Genre
from users.models import User, GenrePreference
from dashboard.models import ViewingHistory

class MLArtifactLoader:
    _instance = None
    _artifacts = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLArtifactLoader, cls).__new__(cls)
        return cls._instance

    def get_artifact(self, name):
        if name not in self._artifacts:
            path = os.path.join(settings.BASE_DIR, 'ml_models', 'artifacts', name)
            if os.path.exists(path):
                if name.endswith('.json'):
                    with open(path, 'r') as f:
                        self._artifacts[name] = json.load(f)
                elif name.endswith('.pkl'):
                    self._artifacts[name] = joblib.load(path)
            else:
                return None
        return self._artifacts.get(name)

loader = MLArtifactLoader()

def _deduplicate_results(queryset, limit=20):
    
    seen = set()
    unique_results = []
    for movie in queryset[:limit * 5]:
        if movie.movie_id not in seen:
            unique_results.append(movie)
            seen.add(movie.movie_id)
        if len(unique_results) >= limit:
            break
    return unique_results

def get_age_bucket(age):
    """Categorizes users into demographic buckets."""
    if age is None or age == 0: return "Unknown"
    if age < 18: return "Teens"
    if age < 30: return "Young Adults"
    if age < 50: return "Adults"
    return "Seniors"

def get_safety_filter():
    """
    Returns a unified safety filter (Q object) to exclude mature/explicit content.
    Balanced to hide Romance/Adult themes while keeping Action/Horror visible.
    """
    ratings_q = Q(content_rating__in=['R', 'NC-17', '18', '18+', 'A', 'Adult', 'TV-MA', 'X'])
    
    genres_q = Q(movie_genres__genre__genre_name__icontains='Adult') | \
               Q(movie_genres__genre__genre_name__icontains='Erotica')
    
    keywords_q = Q(description__icontains='adult') | \
                 Q(description__icontains='sex') | \
                 Q(description__icontains='erotic') | \
                 Q(description__icontains='vulgar') | \
                 Q(description__icontains='porn') | \
                 Q(description__icontains='nudity') | \
                 Q(description__icontains='nude') | \
                 Q(description__icontains='erotica') | \
                 Q(description__icontains='intimacy') | \
                 Q(description__icontains='naked') | \
                 Q(description__icontains='intimate') | \
                 Q(description__icontains='lovemaking') | \
                 Q(description__icontains='bedroom') | \
                 Q(description__icontains='topless') | \
                 Q(description__icontains='intimate scene') | \
                 Q(description__icontains='steamy') | \
                 Q(description__icontains='lust') | \
                 Q(title__icontains='sexy') | \
                 Q(title__icontains='porn') | \
                 Q(title__icontains='adult') | \
                 Q(title__icontains='topless') | \
                 Q(title__iexact='Animal') | \
                 Q(title__iexact='When Night Is Falling') | \
                 Q(title__iexact='Feast of July') | \
                 Q(title__icontains='Bikini') | \
                 Q(title__icontains='Stripper')

    return ratings_q | genres_q | keywords_q

def calculate_match_score(user, movie, source=None, recent_genre_ids=None, recent_langs=None, u_age=None, u_gender=None):
    try:
        base_score = 100
        
        m_lang = (getattr(movie, 'language', '') or '').lower()
        lang_boost = 0
        
        pref_langs = getattr(user, 'language_preference', 'English') or 'English'
        user_langs = [l.strip().lower() for l in pref_langs.split(',') if l.strip()]
        
        if any(ul in m_lang for ul in user_langs):
            lang_boost += 600000 

        if recent_langs:
            if any(rl in m_lang for rl in recent_langs):
                lang_boost = max(lang_boost, 900000) 

            m_genre_ids = [mg.genre_id for mg in movie.movie_genres.all()] if hasattr(movie, '_prefetched_objects_cache') and 'movie_genres' in movie._prefetched_objects_cache else list(movie.movie_genres.values_list('genre_id', flat=True))
            if recent_genre_ids is not None and any(rgid in m_genre_ids for rgid in recent_genre_ids):
                base_score += 400
        
        if source == 'rating' or source == 'history':
            base_score += 85
        elif source == 'profile':
            base_score += 65
        elif source == 'collab':
            base_score -= 10
            
        recent_visual_color = getattr(user, 'current_visual_theme', None)
        if recent_visual_color and movie.dominant_color == recent_visual_color:
            base_score += 100000 
            
        # Apply Demographic Archetype Boosts
        if hasattr(movie, '_prefetched_objects_cache') and 'movie_genres' in movie._prefetched_objects_cache:
            m_genres = [mg.genre.genre_name.lower() for mg in movie.movie_genres.all()]
        else:
            m_genres = [mg.genre.genre_name.lower() for mg in movie.movie_genres.select_related('genre')]

        u_gender = u_gender or (getattr(user, 'gender', 'Other') or 'Other').lower()
        if u_gender == 'male':
            if any(g in m_genres for g in ['action', 'thriller', 'war', 'sci-fi', 'adventure']):
                base_score += 150000
        elif u_gender == 'female':
            if any(g in m_genres for g in ['romance', 'drama', 'family', 'musical', 'fantasy']):
                base_score += 150000
                
        u_age = u_age or getattr(user, 'age', 18) or 18
        if u_age < 18:
            if any(g in m_genres for g in ['animation', 'fantasy', 'adventure', 'family']):
                base_score += 200000
        elif 18 <= u_age <= 30:
            if any(g in m_genres for g in ['sci-fi', 'action', 'romance', 'horror']):
                base_score += 180000
        elif 30 < u_age <= 50:
            if any(g in m_genres for g in ['drama', 'thriller', 'crime', 'mystery', 'history']):
                base_score += 180000
        else: # 50+
            if any(g in m_genres for g in ['history', 'war', 'documentary', 'classic', 'drama']):
                base_score += 200000
            
        return base_score + lang_boost
    except Exception:
        return 85 + (hash(str(movie.movie_id)) % 10)

def apply_match_scores(user, movie_list, source=None, recent_langs=None, recent_genre_ids=None):
    if not movie_list:
        return []

    # Filter out any None values to prevent attribute access errors
    movie_list = [m for m in movie_list if m]
    if not movie_list:
        return []

    from .models import MovieGenre
    from django.db.models import Q
    
    u_age = getattr(user, 'age', 18) or 18
    u_gender = (getattr(user, 'gender', 'Other') or 'Other').lower()
    
    movie_ids = [m.movie_id for m in movie_list]
    
    from .models import Movies
    movie_list_optimized = list(Movies.objects.filter(movie_id__in=movie_ids).prefetch_related('movie_genres__genre').select_related('stats'))
    movie_map = {m.movie_id: m for m in movie_list_optimized}
    
    final_list = []
    
    if recent_langs is None or recent_genre_ids is None:
        recent_langs, recent_genre_ids = get_recent_user_interests(user)
    
    for original_movie in movie_list:
        movie = movie_map.get(original_movie.movie_id, original_movie)
        if not movie:
            continue
            
        score = calculate_match_score(user, movie, source, recent_genre_ids, recent_langs, u_age=u_age, u_gender=u_gender)
        
        movie.match_percentage_raw = score
        # Scale score into a consistent percentage (70% to 99%)
        display_percent = 70 + min(29, int(score / 35000))
        movie.match_percentage = display_percent
        final_list.append(movie)
        
    return final_list

def get_recent_user_interests(user):
    if not user or not getattr(user, 'user_id', None):
        return [], []
    
    from .models import Rating, MovieGenre
    
    recent_ratings = Rating.objects.filter(user=user).filter(Q(score__gte=4) | Q(is_recommended=True)).select_related('movie').order_by('-created_at')[:5]
    
    recent_langs = set()
    recent_genre_ids = set()
    
    for r in recent_ratings:
        if r.movie.language:
            recent_langs.add(r.movie.language.lower().strip())
        
        m_genres = list(MovieGenre.objects.filter(movie=r.movie).values_list('genre_id', flat=True))
        for gid in m_genres:
            recent_genre_ids.add(gid)
            
    return list(recent_langs), list(recent_genre_ids)

def get_smart_recommendations(user):
    if not user or not getattr(user, 'user_id', None):
        # Return fallback recommendations for guest users
        poster_filter = Q(poster_url_external__isnull=False) & ~Q(poster_url_external="")
        safety_filter = get_safety_filter()
        fallback = list(Movies.objects.filter(poster_filter).exclude(safety_filter).order_by('-release_year', '?')[:30])
        return {
            'hybrid': apply_match_scores(user, fallback, source='profile'),
            'cold_start': fallback,
            'user_has_history': False
        }

    seen_ids = set()
    lang_pref_raw = getattr(user, 'language_preference', 'English') or 'English'
    u_lang_prefs = [lp.strip().lower() for lp in lang_pref_raw.split(',') if lp.strip()]

    def _get_unique_scored(movies, source, count=20):
        unique = []
        for m in movies:
            if m and m.movie_id not in seen_ids:
                unique.append(m)
                seen_ids.add(m.movie_id)
            if len(unique) >= count:
                break
        return apply_match_scores(user, unique, source=source, recent_langs=recent_langs, recent_genre_ids=recent_genre_ids)

    def calculate_priority(m):
        if not m: return 0
        m_lang = (getattr(m, 'language', '') or '').lower()
        score = getattr(m, 'match_percentage_raw', 0)
        
        if any(lp in m_lang for lp in u_lang_prefs):
            score += 5000000
            
        if any(rl in m_lang for rl in recent_langs):
            score += 3000000
            
        m_genre_ids = [mg.genre_id for mg in m.movie_genres.all()] if hasattr(m, 'movie_genres') else []
        if any(rgid in m_genre_ids for rgid in recent_genre_ids):
            score += 1000000
            
        return score

    recommendations = {
        'demographic': [],
        'history_based': [],
        'collaborative': [],
        'visual_content': [],
        'poster_based': [],
        'chromatic_harmony': [],
        'visual_theme_name': None,
        'rating_based': [],
        'collaborative_based': [],
        'duration_based': [],
        'hybrid': [],
        'cold_start': [],
        'user_has_history': False
    }


    visual_features = loader.get_artifact('visual_features.json') or {}
    tfidf_matrix = loader.get_artifact('tfidf_matrix.pkl')
    ranking_model = loader.get_artifact('ranking_model.pkl')

    poster_filter = Q(poster_url_external__isnull=False) & ~Q(poster_url_external="")
    safety_filter = get_safety_filter()

    if not user:
        recs = _deduplicate_results(Movies.objects.filter(poster_filter).exclude(safety_filter).order_by('-release_year', '?'), limit=20)
        recommendations['hybrid'] = recs
        recommendations['cold_start'] = recs
        return recommendations

    recent_langs, recent_genre_ids = get_recent_user_interests(user)
    recent_interests = (recent_langs, recent_genre_ids)

    use_safety = getattr(user, 'adult_content_filter', True) or (user.age is not None and user.age < 18)
    user_ratings = Rating.objects.filter(user=user)
    user_history = ViewingHistory.objects.filter(user=user)
    

    disliked_ids = user_ratings.filter(Q(score__lt=3) | Q(is_recommended=False)).values_list('movie_id', flat=True)
    skipped_ids = user_history.filter(progress__lt=0.1).values_list('movie_id', flat=True)
    watched_ids = list(user_history.filter(progress__gte=0.9).values_list('movie_id', flat=True))
    exclude_ids = list(set(list(disliked_ids) + list(skipped_ids) + list(watched_ids)))

    all_good_ratings_qs = user_ratings.filter(Q(score__gte=3) | Q(is_recommended=True)).order_by('-created_at')
    latest_seeds_ids = list(all_good_ratings_qs[:5].values_list('movie_id', flat=True))
    all_seeds_ids = list(all_good_ratings_qs.values_list('movie_id', flat=True))
    
    recent_seed_genres = list(MovieGenre.objects.filter(movie_id__in=latest_seeds_ids).values_list('genre_id', flat=True).distinct())
    all_seed_genres = list(MovieGenre.objects.filter(movie_id__in=all_seeds_ids).values_list('genre_id', flat=True).distinct())

    direct_sim_ids = set()
    for sid in latest_seeds_ids[:3]:
        try:
            m_seed = Movies.objects.get(movie_id=sid)
            rel_sim = get_related_movies(m_seed, limit=10)
            for rm in rel_sim:
                direct_sim_ids.add(rm.movie_id)
        except: pass
    
    liked_movie_ids = list(set(
        list(user_history.filter(progress__gte=0.2).values_list('movie_id', flat=True)) +
        list(user_ratings.filter(score__gte=3).values_list('movie_id', flat=True))
    ))
    
    liked_genre_ids = MovieGenre.objects.filter(movie_id__in=liked_movie_ids).values_list('genre_id', flat=True).distinct()

    lang_pref_raw = getattr(user, 'language_preference', 'English') or 'English'
    u_lang_prefs = [lp.strip().lower() for lp in lang_pref_raw.split(',') if lp.strip()]
    
    if u_lang_prefs:
        real_excluded = []
        for eid in exclude_ids:
            try:
                m = Movies.objects.get(movie_id=eid)
                m_lang = (m.language or '').lower()
                if any(lp in m_lang for lp in u_lang_prefs):
                    if user_ratings.filter(movie_id=eid, score__lt=3).exists():
                         real_excluded.append(eid)
                else:
                    real_excluded.append(eid)
            except:
                real_excluded.append(eid)
        exclude_ids = real_excluded

    recommendations['user_has_history'] = user_ratings.exists() or user_history.filter(progress__gte=0.1).exists()

    recent_watched_ids = list(user_history.order_by('-watched_at')[:5].values_list('movie_id', flat=True))
    visual_seed_ids = list(dict.fromkeys(recent_watched_ids + liked_movie_ids))[:10]

    # Base pool with safety and exclusions
    base_qs = Movies.objects.filter(poster_filter).exclude(movie_id__in=exclude_ids)

    if use_safety:
        base_qs = base_qs.exclude(safety_filter)
        base_qs = base_qs.exclude(movie_genres__genre__genre_name__icontains='Romance')
        base_qs = base_qs.exclude(movie_genres__genre__genre_name__icontains='Erotica')
    
    if user.age is not None and user.age < 16:
        base_qs = base_qs.exclude(movie_genres__genre__genre_name__icontains='Crime')

    base_qs = base_qs.select_related('stats')

    # Genre-specific pool
    rec_qs = base_qs
    from users.models import GenrePreference
    pref_genre_ids = set(GenrePreference.objects.filter(user=user).values_list('genre_id', flat=True))
    
    if pref_genre_ids:
        rec_qs = base_qs.filter(movie_genres__genre__genre_id__in=pref_genre_ids).distinct()


    visual_features = loader.get_artifact('visual_features.json') or {}
    
    user_visual_profile = {
        'avg_brightness': 128,
        'avg_saturation': 128,
        'preferred_vibes': {},
        'preferred_styles': {},
        'color_palette': []
    }

    if user_history.exists():
        history_ids = [str(m.movie.movie_id) for m in user_history.filter(progress__gte=10).order_by('-watched_at')[:5]]
        relevant_features = [visual_features[mid] for mid in history_ids if mid in visual_features]
        
        if relevant_features:
            user_visual_profile['avg_brightness'] = np.mean([f['brightness'] for f in relevant_features])
            user_visual_profile['avg_saturation'] = np.mean([f['saturation'] for f in relevant_features])
            
            for f in relevant_features:
                v = f.get('vibe', 'Standard')
                s = f.get('visual_style', 'Cinematic')
                user_visual_profile['preferred_vibes'][v] = user_visual_profile['preferred_vibes'].get(v, 0) + 1
                user_visual_profile['preferred_styles'][s] = user_visual_profile['preferred_styles'].get(s, 0) + 1
                if 'palette' in f:
                    user_visual_profile['color_palette'].extend([p['hex'] for p in f['palette']])

    pref_vibe_raw = max(user_visual_profile['preferred_vibes'].keys(), key=lambda k: user_visual_profile['preferred_vibes'][k], default="Standard")
    pref_style_raw = max(user_visual_profile['preferred_styles'].keys(), key=lambda k: user_visual_profile['preferred_styles'][k], default="Cinematic")


    vibe_map = {
        "Noir/Dark": "Moody",
        "Neon/Vibrant": "Vibrant",
        "Pastel/Soft": "Soft",
        "Desaturated/Gritty": "Gritty",
        "Standard": "Cinematic"
    }
    style_map = {
        "Action-Packed/Complex": "Dynamic",
        "Minimalist": "Clean",
        "Cinematic": "Aesthetic"
    }

    v_simple = vibe_map.get(pref_vibe_raw, "Cinematic")
    s_simple = style_map.get(pref_style_raw, "Visuals")
    
    recommendations['visual_theme_name'] = f"{v_simple} & {s_simple}" if v_simple != "Cinematic" else f"{s_simple} Style"

    visual_candidates = []
    for movie in rec_qs[:300]:
        m_id = str(movie.movie_id)
        if m_id in visual_features:
            feat = visual_features[m_id]
            v_score = 0
            if feat.get('vibe') == pref_vibe_raw: v_score += 50
            if feat.get('visual_style') == pref_style_raw: v_score += 30
            
            v_score += max(0, 20 - abs(feat['brightness'] - user_visual_profile['avg_brightness']) / 10)
            v_score += max(0, 20 - abs(feat['saturation'] - user_visual_profile['avg_saturation']) / 10)
            
            setattr(movie, 'visual_match_score', v_score)
            visual_candidates.append(movie)

    visual_candidates.sort(key=lambda m: getattr(m, 'visual_match_score', 0), reverse=True)
    top_visual = visual_candidates[:60]
    import random
    random.shuffle(top_visual)
    
    recommendations['poster_based'] = apply_match_scores(user, top_visual[:20], source='poster')
    recommendations['chromatic_harmony'] = apply_match_scores(user, top_visual[20:40] if len(top_visual) > 20 else [], source='poster')


    visual_recs = []
    if liked_movie_ids:
        raw_v = rec_qs.filter(movie_genres__genre_id__in=liked_genre_ids).order_by('-release_year', '?')
        visual_recs = _deduplicate_results(sorted(raw_v, key=lambda m: 1 if any(lp.lower() in (getattr(m, 'language', '') or '').lower() for lp in u_lang_prefs) else 0, reverse=True), 60)
    else:
        visual_recs = _deduplicate_results(rec_qs.order_by('?'), 60)

    random.shuffle(visual_recs)

    if not visual_recs:
        visual_recs = _deduplicate_results(rec_qs.order_by('?'), 20)
        
    recommendations['visual_content'] = apply_match_scores(user, visual_recs[:20], source='poster')


    lang_q = Q()

    for lp in u_lang_prefs:
        lang_q |= Q(language__icontains=lp)
        lang_q |= Q(movie_genres__genre__genre_name__icontains=lp)
    
    if not lang_q:
        lang_q = Q(pk=-1)
    

    rec_qs = rec_qs.exclude(movie_id__in=exclude_ids)
    

    # Fetch language matches from the entire safe pool (base_qs), not just genres
    lang_matches = base_qs.filter(lang_q).order_by('-release_year', '-stats__avg_rating')[:100]
    
    generic_pref_q = Q(movie_genres__genre__genre_id__in=pref_genre_ids)
    # Use base_qs for pref_results so that favored languages are included even if they aren't in favored genres
    pref_results_qs = base_qs.filter(generic_pref_q | lang_q).annotate(
        is_lang=Case(When(lang_q, then=Value(1)), default=Value(0), output_field=IntegerField())
    ).order_by('-is_lang', '-release_year', '-stats__avg_rating', '?')
    
    pref_results = _deduplicate_results(pref_results_qs, 300)

    
    recommendations['demographic'] = pref_results[:20]


    duration_recs = _deduplicate_results(rec_qs.filter(duration__lte=105).order_by('?'), 20)
    recommendations['duration_based'] = apply_match_scores(user, duration_recs, source='profile')


    all_candidates = list(lang_matches) + list(pref_results) + list(recommendations['poster_based']) + list(visual_recs)
    
    unique_candidates_map = {}
    for m in all_candidates:
        if m.movie_id not in unique_candidates_map:
            unique_candidates_map[m.movie_id] = m
    
    unique_candidates = list(unique_candidates_map.values())[:300]
    
    u_lang_prefs = [lp.strip().lower() for lp in lang_pref_raw.split(',') if lp.strip()]
    
    unique_candidates.sort(key=calculate_priority, reverse=True)
    
    unique_candidates = apply_match_scores(user, unique_candidates, source='profile', recent_langs=recent_langs, recent_genre_ids=recent_genre_ids)
    
    unique_candidates.sort(key=calculate_priority, reverse=True)


    recommendations['hybrid'] = _get_unique_scored(unique_candidates, source='profile', count=60)
    


    recommendations['demographic'] = _get_unique_scored(recommendations['demographic'], source='profile')
    

    recommendations['poster_based'] = _get_unique_scored(recommendations['poster_based'], source='poster')
    recommendations['visual_content'] = _get_unique_scored(recommendations['visual_content'], source='poster')
    recommendations['chromatic_harmony'] = _get_unique_scored(recommendations.get('chromatic_harmony', []), source='poster')
    recommendations['duration_based'] = _get_unique_scored(recommendations['duration_based'], source='profile')


    recommendations['cold_start'] = _get_unique_scored(list(pref_results[:15]) + list(duration_recs[:10]), source='profile')


    user_engaged_enough = user_history.filter(progress__gte=20).exists()
    
    user_good_ratings = list(user_ratings.filter(Q(score__gte=3) | Q(is_recommended=True)).values_list('movie_id', flat=True))
    if user_good_ratings:
        seed_movies = Movies.objects.filter(movie_id__in=user_good_ratings)
        seed_genres = list(MovieGenre.objects.filter(movie__in=seed_movies).values_list('genre_id', flat=True).distinct())
        
        seed_langs = list(set([m.language.lower() for m in seed_movies if m.language]))
        rated_lang_q = Q()
        for sl in seed_langs:
            rated_lang_q |= Q(language__icontains=sl)
            
        if not rated_lang_q:
            rated_lang_q = Q(pk=-1)
            
        final_lang_q = rated_lang_q
        primary_lang_q = Q(pk=-1)
        if recent_langs:
             recent_lang_q = Q()
             for rl in recent_langs:
                 recent_lang_q |= Q(language__icontains=rl)
             final_lang_q = recent_lang_q
             primary_lang_q = recent_lang_q
        
        if not primary_lang_q:
            primary_lang_q = Q(pk=-1)
        if not rated_lang_q:
            rated_lang_q = Q(pk=-1)
        if not final_lang_q:
            final_lang_q = Q(pk=-1)

        rating_filtered_qs = rec_qs.filter(movie_genres__genre__genre_id__in=seed_genres)\
            .filter(final_lang_q)\
            .annotate(
                r_count=Count('rating'),
                is_recent_match=Case(When(primary_lang_q & Q(movie_genres__genre__genre_id__in=recent_genre_ids), then=Value(100)), default=Value(0), output_field=IntegerField()),
                is_direct_sim=Case(When(movie_id__in=list(direct_sim_ids), then=Value(50)), default=Value(0), output_field=IntegerField()),
                is_latest_genre=Case(When(movie_genres__genre__genre_id__in=recent_genre_ids, then=Value(30)), default=Value(0), output_field=IntegerField()),
                is_recent_lang=Case(When(primary_lang_q, then=Value(20)), default=Value(0), output_field=IntegerField()),
                strict_lang_match=Case(When(rated_lang_q, then=Value(10)), default=Value(0), output_field=IntegerField())
            ).order_by('-is_recent_match', '-is_direct_sim', '-is_latest_genre', '-is_recent_lang', '-strict_lang_match', '-stats__avg_rating', '?')
        
        rating_recs = _deduplicate_results(rating_filtered_qs, limit=25)
        
        if len(rating_recs) < 8:
            filler_qs = rec_qs.filter(movie_genres__genre__genre_id__in=seed_genres).filter(rated_lang_q).exclude(movie_id__in=[m.movie_id for m in rating_recs])
            rating_recs.extend(_deduplicate_results(filler_qs, limit=(15 - len(rating_recs))))

        apply_match_scores(user, rating_recs, source='rating', recent_langs=recent_langs, recent_genre_ids=recent_genre_ids)
        recommendations['rating_based'] = sorted(rating_recs, key=lambda x: getattr(x, 'match_percentage_raw', 0), reverse=True)
    else:
        recommendations['rating_based'] = []
    
    recommendations['collaborative_based'] = _get_unique_scored(rec_qs.annotate(v_count=Count('viewinghistory')).order_by('-v_count'), source='collab')
    

    if liked_movie_ids:
        movie_popularity = ViewingHistory.objects.filter(movie_id__in=liked_movie_ids).values('movie_id').annotate(count=Count('user_id'))
        pop_map = {m['movie_id']: m['count'] for m in movie_popularity}
        
        potential_soulmates = {}
        history_matches = ViewingHistory.objects.filter(movie_id__in=liked_movie_ids, progress__gte=60).exclude(user=user).select_related('user')
        
        for record in history_matches:
            pop = pop_map.get(record.movie.movie_id, 10)
            weight = 1.0 / (np.log1p(pop) + 1)
            potential_soulmates[record.user.user_id] = potential_soulmates.get(record.user.user_id, 0) + weight

        sorted_soulmates = sorted(potential_soulmates.items(), key=lambda x: x[1], reverse=True)[:20]
        soulmate_ids = [s[0] for s in sorted_soulmates]
        soulmate_weights = {s[0]: s[1] for s in sorted_soulmates}

        if soulmate_ids:
            true_collab_qs = rec_qs.exclude(movie_id__in=liked_movie_ids).filter(
                Q(viewinghistory__user_id__in=soulmate_ids, viewinghistory__progress__gte=60) | 
                Q(rating__user_id__in=soulmate_ids, rating__score__gte=4)
            ).distinct()
            
            collab_candidates = []
            
            u_lang_prefs_lower = [lp.lower() for lp in u_lang_prefs]

            for movie in true_collab_qs[:100]:
                m_id = movie.movie_id
                score = 0
                vh = ViewingHistory.objects.filter(user_id__in=soulmate_ids, movie_id=m_id, progress__gte=60)
                for record in vh:
                    score += soulmate_weights.get(record.user.user_id, 0) * 2
                
                rt = Rating.objects.filter(user_id__in=soulmate_ids, movie_id=m_id, score__gte=4)
                for record in rt:
                    score += soulmate_weights.get(record.user.user_id, 0) * 3
                
                m_lang = (getattr(movie, 'language', '') or '').lower()
                if any(lp in m_lang for lp in u_lang_prefs_lower):
                    score *= 2.0
                
                setattr(movie, 'collab_score', score)
                collab_candidates.append(movie)
                
            collab_candidates.sort(key=lambda m: getattr(m, 'collab_score', 0), reverse=True)
            
            if not collab_candidates:
                fallback_qs = rec_qs.exclude(movie_id__in=liked_movie_ids).filter(
                    movie_genres__genre_id__in=liked_genre_ids
                ).annotate(
                    fallback_count=Count('viewinghistory')
                ).order_by('-stats__avg_rating', '-fallback_count')
                collab_candidates = list(fallback_qs[:10])
                
            recommendations['true_collaborative'] = apply_match_scores(user, collab_candidates[:20], source='collab')
        else:
            fallback_qs = rec_qs.exclude(movie_id__in=liked_movie_ids).filter(
                movie_genres__genre_id__in=liked_genre_ids
            ).annotate(
                fallback_count=Count('viewinghistory')
            ).order_by('-stats__avg_rating', '-fallback_count')
            recommendations['true_collaborative'] = apply_match_scores(user, list(fallback_qs[:10]), source='collab')
    else:
        recommendations['true_collaborative'] = []
    

    history_recs = []
    if liked_movie_ids:

        seed_data = Movies.objects.filter(movie_id__in=liked_movie_ids)
        seed_genres = list(MovieGenre.objects.filter(movie__in=seed_data).values_list('genre_id', flat=True).distinct())
        seed_langs = list(set([m.language for m in seed_data if m.language]))
        

        deep_dive_q = Q(movie_genres__genre_id__in=seed_genres)
        lang_match_q = Q()
        for sl in seed_langs:
            lang_match_q |= Q(language__icontains=sl)
            
        if not lang_match_q:
            lang_match_q = Q(pk=-1)
            

        dive_qs = rec_qs.filter(deep_dive_q).annotate(
            is_lang_match=Case(When(lang_match_q, then=Value(1)), default=Value(0), output_field=IntegerField())
        ).order_by('-is_lang_match', '-release_year', '-stats__avg_rating')
        
        history_recs = _deduplicate_results(dive_qs, limit=30)
        
    recommendations['history_based'] = apply_match_scores(user, history_recs, source='history', recent_langs=recent_langs, recent_genre_ids=recent_genre_ids)

    return recommendations





def get_related_movies(movie, limit=15, user=None):
    
    genre_ids = list(movie.movie_genres.values_list('genre_id', flat=True)) if movie else []
    if not movie: return []
    
    is_animation = movie.movie_genres.filter(genre__genre_name__icontains='Animation').exists()
    
    m_lang = movie.language or ""
    lang_q = Q(language__icontains=m_lang) if m_lang else Q(pk=-1)
    
    related_qs = Movies.objects.filter(movie_genres__genre_id__in=genre_ids).exclude(pk=movie.movie_id)
    
    if user:
        from users.models import GenrePreference
        pref_genre_ids = set(GenrePreference.objects.filter(user=user).values_list('genre_id', flat=True))
        if pref_genre_ids:
            related_qs = related_qs.filter(movie_genres__genre__genre_id__in=pref_genre_ids)
            
    related_qs = related_qs.annotate(

        genre_overlap=Count('movie_genres', filter=Q(movie_genres__genre_id__in=genre_ids)),
        category_boost=Case(When(movie_genres__genre__genre_name__icontains='Animation' if is_animation else 'Action_Fake_Genre', then=Value(10)), default=Value(0), output_field=IntegerField()),
        lang_match=Case(When(lang_q, then=Value(50)), default=Value(0), output_field=IntegerField())
    ).filter(poster_url_external__isnull=False)
    
    related_qs = related_qs.order_by('-lang_match', '-category_boost', '-genre_overlap', '-stats__avg_rating', '-release_year')[:limit * 2]
    
    seen = set()
    results = []
    for m in related_qs:
        if m.movie_id not in seen:
            results.append(m)
            seen.add(m.movie_id)
        if len(results) >= limit:
            break
            
    if user:
         r_langs, r_gids = get_recent_user_interests(user)
         results = apply_match_scores(user, results, source='standard', recent_langs=r_langs, recent_genre_ids=r_gids)
    
    return results
