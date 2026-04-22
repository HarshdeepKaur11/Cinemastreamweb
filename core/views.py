from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib import messages
from .models import ContactMessage
from users.models import User, GenrePreference
from ml_models.models import Movies, Genre
from ml_models.utils import get_smart_recommendations
from dashboard.models import SearchHistory
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import logging

logger = logging.getLogger(__name__)

def index_view(request):
    if request.session.get('user_id'):
        return redirect('dashboard:user_dashboard')

    movies_queryset = Movies.objects.filter(poster_url_external__isnull=False).exclude(poster_url_external="").distinct()

    trending_movies = movies_queryset.annotate(
        watch_count=models.Count('viewinghistory')
    ).order_by('-watch_count', '-release_year')[:10]

    latest_movies = movies_queryset.order_by('-release_year', '-movie_id')[:8]

    featured_movie = movies_queryset.filter(release_year__gte=2025).order_by('?').first() or movies_queryset.order_by('?').first()

    return render(request, 'core/index.html', {
        'featured_movie': featured_movie,
        'trending_movies': trending_movies,
        'latest_movies': latest_movies
    })

def contact_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None

    if request.method == 'POST':
        if not user:
            messages.error(request, 'You must be logged in to send inquiries.')
            return redirect('users:login')

        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and subject and message:
            ContactMessage.objects.create(
                user=user,
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('core:contact')
        else:
            messages.error(request, 'Please fill in all fields.')

    return render(request, 'core/contact.html', {'current_user': user})

def learn_more_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None
    return render(request, 'core/learnmore.html', {'current_user': user})

def security_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None

    if not user:
        return redirect('users:login')

    if request.method == "POST":
        action = request.POST.get('action')

        if action == 'change_email':
            new_email = request.POST.get('new_email', '').strip()
            if not new_email:
                messages.error(request, "Please provide a new email address.")
                return redirect('core:security')

            if new_email == user.email:
                messages.error(request, "New email must be different from current email.")
                return redirect('core:security')

            if User.objects.filter(email=new_email).exclude(user_id=user.user_id).exists():
                messages.error(request, "This email is already registered to another account.")
                return redirect('core:security')

            otp = str(random.randint(100000, 999999))

            request.session['pending_new_email'] = new_email
            request.session['email_change_otp'] = otp
            request.session['email_otp_created_at'] = timezone.now().isoformat()

            subject_new = "CinemaStream Email Verification"
            message_new = f"Hi {user.username or 'there'},\n\nYour verification code to update your registered email is: {otp}\n\nPlease enter this code to finalize the update. This code will expire in 5 minutes.\n\nHappy Streaming!\nCinemastream Team"

            subject_old = "Security Alert: Email Change Initiated"
            message_old = f"Hi {user.username or 'there'},\n\nWe noticed a request to change the registered email for your account to: {new_email}.\n\nIf you did not initiate this request, please change your password immediately and contact support.\n\nCinemaStream Security Team"

            try:
                send_mail(subject_new, message_new, settings.EMAIL_HOST_USER, [new_email], fail_silently=False)

                try:
                    send_mail(subject_old, message_old, settings.EMAIL_HOST_USER, [user.email], fail_silently=True)
                except Exception as e:
                    logger.warning("Failed to send security alert to old email %s: %s", user.email, e)

                messages.success(request, f"A verification code has been sent to {new_email}. Please check your inbox!")
                return redirect('core:verify_email_change')
            except Exception as e:
                messages.error(request, f"Error sending verification email: {str(e)}. Please check your internet connection.")
                return redirect('core:security')

        from django.contrib.auth.hashers import check_password, make_password

        curr_pass = request.POST.get('current_password', '').strip()
        new_pass = request.POST.get('new_password', '').strip()
        conf_pass = request.POST.get('confirm_password', '').strip()

        if not curr_pass or not new_pass or not conf_pass:
            messages.error(request, "Please fill in all password fields.")
            return redirect('core:security')

        if not check_password(curr_pass, user.password):
            messages.error(request, "Incorrect current password!")
            return redirect('core:security')

        if new_pass != conf_pass:
            messages.error(request, "Passwords do not match!")
            return redirect('core:security')

        if len(new_pass) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('core:security')

        user.password = make_password(new_pass)
        user.password_last_updated = timezone.now()
        user.save()
        messages.success(request, "Password updated successfully!")
        return redirect('core:security')

    return render(request, 'core/security.html', {'current_user': user})

def setting_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None

    if not user:
        return redirect('users:login')

    if request.method == "POST":
        dur = request.POST.get('duration_preference')

        adult_filter = 'adult_content_filter' in request.POST

        has_changes = False

        if dur and dur != user.duration_preference:
            user.duration_preference = dur
            has_changes = True

        if user.age and user.age < 18:
            adult_filter = True

        if adult_filter != user.adult_content_filter:
            user.adult_content_filter = adult_filter
            has_changes = True

            if not adult_filter:
                from ml_models.models import Genre
                from users.models import GenrePreference
                from django.db.models import Q

                mature_genres = Genre.objects.filter(Q(genre_name__icontains='Romance') | Q(genre_name__icontains='Erotica'))
                for g in mature_genres:
                    GenrePreference.objects.get_or_create(user=user, genre=g)

        if has_changes:
            user.save()

            from django.core.cache import cache
            cache.delete(f"user_dash_v16_{user.user_id}")
            messages.success(request, 'Settings have been updated successfully!')

        return redirect('core:setting')

    return render(request, 'core/setting.html', {'current_user': user})

def search_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None
    query = request.GET.get('q')
    movies = []

    if query:

        SearchHistory.objects.create(user=user, query=query[:255])

        from ml_models.utils import get_safety_filter
        safety_filter = get_safety_filter()

        if user:
            use_safety = getattr(user, 'adult_content_filter', True) or (user.age is not None and user.age < 18)
        else:
            use_safety = True

        movies_qs = Movies.objects.filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(language__icontains=query) |
            models.Q(movie_genres__genre__genre_name__icontains=query) |
            models.Q(movie_casts__person__name__icontains=query)
        )

        if use_safety:

            movies_qs = movies_qs.exclude(safety_filter)
            movies_qs = movies_qs.exclude(movie_genres__genre__genre_name__icontains='Romance')
            movies_qs = movies_qs.exclude(movie_genres__genre__genre_name__icontains='Erotica')
            movies_qs = movies_qs.exclude(movie_genres__genre__genre_name__icontains='Adult')

        movies = movies_qs.select_related('stats').distinct()

        from ml_models.utils import apply_match_scores
        movies = apply_match_scores(user, movies, source='search')

    return render(request, 'core/search_movies.html', {
        'query': query,
        'movies': movies,
        'current_user': user
    })

@csrf_protect
def toggle_genre_preference(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        import json
        data = json.loads(request.body)
        genre_id = data.get('genre_id')

        if not genre_id:
            return JsonResponse({'status': 'error', 'message': 'Genre ID required'}, status=400)

        user = User.objects.get(user_id=user_id)
        genre = get_object_or_404(Genre, genre_id=genre_id)

        pref = GenrePreference.objects.filter(user=user, genre=genre).first()
        if pref:
            pref.delete()
            action = 'removed'
        else:
            GenrePreference.objects.create(user=user, genre=genre)
            action = 'added'

        return JsonResponse({'status': 'success', 'action': action})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def verify_email_change_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None

    if not user:
        return redirect('users:login')

    pending_email = request.session.get('pending_new_email')
    stored_otp = request.session.get('email_change_otp')
    otp_time_str = request.session.get('email_otp_created_at')

    if not pending_email or not stored_otp:
        messages.error(request, "No email change request found.")
        return redirect('core:security')

    if request.method == "POST":
        entered_otp = request.POST.get('otp', '').strip()

        from datetime import datetime
        otp_time = datetime.fromisoformat(otp_time_str) if otp_time_str else timezone.now()
        if (timezone.now() - otp_time).total_seconds() > 300:
            messages.error(request, "Verification code has expired. Please request a new one.")
            return redirect('core:verify_email_change')

        if entered_otp == stored_otp:
            user.email = pending_email
            user.save()

            try:
                del request.session['pending_new_email']
                del request.session['email_change_otp']
                del request.session['email_otp_created_at']
            except KeyError:
                pass

            messages.success(request, f"Email address updated successfully to {pending_email}!")
            return redirect('core:security')
        else:
            messages.error(request, "Invalid verification code.")

    return render(request, 'core/verify_email_otp.html', {'pending_email': pending_email})

def resend_email_change_otp_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None

    if not user:
        return redirect('users:login')

    pending_email = request.session.get('pending_new_email')
    if not pending_email:
        messages.error(request, "Session expired. Please try again.")
        return redirect('core:security')

    otp = str(random.randint(100000, 999999))
    request.session['email_change_otp'] = otp
    request.session['email_otp_created_at'] = timezone.now().isoformat()

    subject = "Your New CinemaStream Verification Code"
    message = f"Hi {user.username or 'there'},\n\nYour new verification code is: {otp}\n\nPlease enter this to update your registered email."

    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [pending_email], fail_silently=False)
        messages.success(request, f"A new verification code has been sent to {pending_email}")
    except Exception as e:
        messages.error(request, f"Error sending email: {str(e)}")

    return redirect('core:verify_email_change')

def faq_view(request):
    user_id = request.session.get('user_id')
    user = User.objects.filter(user_id=user_id).first() if user_id else None
    return render(request, 'core/faq.html', {'current_user': user})