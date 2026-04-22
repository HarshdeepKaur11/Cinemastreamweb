from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from django.db.models import Q
from .models import User
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.conf import settings
import random
import uuid
import logging
from .decorators import login_required_custom

logger = logging.getLogger(__name__)

def signup_view(request):
    if request.method == "POST":
        mail = request.POST.get('email', '').strip()
        uname = request.POST.get('username', '').strip()
        pw = request.POST.get('password')
        u_age = request.POST.get('age')
        u_gender = request.POST.get('gender')

        if User.objects.filter(email__iexact=mail).exists():
            messages.error(request, "This email is already registered. Please login or use a different email.")
            return redirect('users:signup')

        if uname:
            if " " in uname:
                messages.error(request, "Username cannot contain spaces.")
                return redirect('users:signup')
            if User.objects.filter(username__iexact=uname).exists():
                messages.error(request, "This username is already taken. Please choose another one.")
                return redirect('users:signup')

        otp = str(random.randint(100000, 999999))

        try:
            with transaction.atomic():
                new_user = User.objects.create(
                    username=uname,
                    email=mail,
                    password=make_password(pw),
                    age=u_age if u_age else 0,
                    gender=u_gender if u_gender else 'Other',
                    is_verified=False,
                    verification_token=otp,
                    otp_created_at=timezone.now(),
                    password_last_updated=timezone.now(),
                    is_admin=False
                )
        except Exception as e:
            logger.exception("Signup error for email %s", mail)
            messages.error(request, "An error occurred during signup. The email or username might already be in use.")
            return redirect('users:signup')

        subject = "Your CinemaStream Verification Code"
        message = f"Hi {uname},\n\nYour verification code is: {otp}\n\nPlease enter this code to verify your account.\n\nHappy Streaming!\nCinemastream Team"

        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [mail], fail_silently=False)
            request.session['unverified_user_id'] = new_user.user_id
            messages.success(request, f"Verification code sent to {mail}. Please check your inbox!")
            return redirect('users:verify_signup_otp')
        except Exception as e:
            logger.exception("Error sending verification email to %s", mail)
            messages.error(request, f"Error sending verification email: {str(e)}")
            if 'new_user' in locals():
                new_user.delete()
            return redirect('users:signup')

    return render(request, 'users/signup.html')

def verify_signup_otp_view(request):
    user_id = request.session.get('unverified_user_id')
    if not user_id:
        return redirect('users:signup')

    user = get_object_or_404(User, user_id=user_id)

    if request.method == "POST":
        entered_otp = request.POST.get('otp')

        if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() > 300:
            messages.error(request, "Verification code has expired. Please request a new one.")
            return redirect('users:verify_signup_otp')

        if entered_otp == user.verification_token:
            user.is_verified = True
            user.verification_token = None
            user.otp_created_at = None
            user.save()

            try:
                from ml_models.models import Genre
                from users.models import GenrePreference
                exclude_list = ['English', 'Hindi', 'Punjabi', 'Spanish', 'French', 'Japanese', 'Korean', 'Musical', 'New Release', 'AI Specials', 'Sci-Fi', 'Romance', 'Erotica', 'Adult']
                all_genres_qs = Genre.objects.exclude(genre_name__in=exclude_list)
                
                if user.age is not None and user.age < 16:
                    all_genres_qs = all_genres_qs.exclude(genre_name__icontains='Crime')
                
                all_genres = list(all_genres_qs)

                existing_prefs = set(GenrePreference.objects.filter(user=user).values_list('genre_id', flat=True))
                genre_prefs = [GenrePreference(user=user, genre=g) for g in all_genres if g.genre_id not in existing_prefs]
                if genre_prefs:
                    GenrePreference.objects.bulk_create(genre_prefs)
            except Exception as e:
                logger.error("Error setting default genre preferences for user %s: %s", user.user_id, e)
                pass

            request.session['user_id'] = user.user_id
            del request.session['unverified_user_id']

            messages.success(request, "OTP Verified! Welcome to Cinemastream.")

            return redirect(reverse('dashboard:user_dashboard') + '?new_user=1')
        else:
            messages.error(request, "Invalid verification code.")

    return render(request, 'users/verify_signup_otp.html', {'email': user.email})

def resend_signup_otp_view(request):
    user_id = request.session.get('unverified_user_id')
    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('users:signup')

    user = get_object_or_404(User, user_id=user_id)

    otp = str(random.randint(100000, 999999))
    user.verification_token = otp
    user.otp_created_at = timezone.now()
    user.save()

    subject = "Your New CinemaStream Verification Code"
    message = f"Hi {user.username},\n\nYour new verification code is: {otp}\n\nPlease enter this code to verify your account.\n\nHappy Streaming!\nCinemastream Team"

    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
        messages.success(request, f"A new verification code has been sent to {user.email}")
    except Exception as e:
        messages.error(request, f"Error sending email: {str(e)}")

    return redirect('users:verify_signup_otp')

def mock_2fa_view(request):
    return render(request, 'users/mock_2fa.html')

def verify_mock_2fa_view(request):
    temp_id = request.session.get('temp_user_id')
    if not temp_id:
        return redirect('users:login')

    if request.method == "POST":
        code = request.POST.get('code')
        user = get_object_or_404(User, user_id=temp_id)

        if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() > 300:
            messages.error(request, "Verification code has expired. Please request a new one.")
            return redirect('users:verify_mock_2fa')

        if code == user.two_fa_code:
            request.session['user_id'] = user.user_id
            user.two_fa_code = None
            user.otp_created_at = None
            user.save()
            try:
                del request.session['temp_user_id']
            except KeyError:
                pass

            from ml_models.utils import get_smart_recommendations
            recs = get_smart_recommendations(user)
            messages.success(request, f"2FA Verified! Welcome back, {user.username}.")

            from users.models import GenrePreference
            has_preferences = GenrePreference.objects.filter(user=user).exists()

            if user.is_admin:
                return redirect('admin_panel:admin_dashboard')

            if has_preferences or recs.get('user_has_history'):

                return redirect('dashboard:user_dashboard')
            else:

                messages.info(request, "Welcome! Please select your favorite genres to get started.")
                return redirect('dashboard:user_dashboard')
        else:
            messages.error(request, "Verification code is incorrect.")
            return render(request, 'users/mock_2fa.html', {'error': 'Verification code is incorrect'})

    return render(request, 'users/mock_2fa.html')

def resend_2fa_otp_view(request):
    temp_id = request.session.get('temp_user_id')
    if not temp_id:
        messages.error(request, "Session expired. Please login again.")
        return redirect('users:login')

    user = get_object_or_404(User, user_id=temp_id)

    code = str(random.randint(1000, 9999))
    user.two_fa_code = code
    user.otp_created_at = timezone.now()
    user.save()

    try:
        send_mail(
            'CinemaStream Login Code',
            f'Your new verification code is: {code}',
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, f"A new verification code has been sent to {user.email}")
    except Exception as e:
        logger.exception("Error resending 2FA OTP for user %s", user.user_id)
        messages.error(request, f"Error sending email: {str(e)}")

    return redirect('users:verify_mock_2fa')

@login_required_custom
def select_genres_view(request):
    from ml_models.models import Genre
    from users.models import GenrePreference
    from django.db.models import Count

    exclude_list = [
        'English', 'Hindi', 'Punjabi', 'Spanish', 'French', 'Japanese', 'Korean',
        'Crime', 'Musical', 'New Release', 'AI Specials', 'Sci-Fi'
    ]
    user = request.current_user
    genres_qs = Genre.objects.annotate(movie_count=Count('movie_genres')).filter(movie_count__gt=0).exclude(genre_name__in=exclude_list)
    if user:
        use_safety = getattr(user, 'adult_content_filter', True) or (user.age is not None and user.age < 18)
        if use_safety:
            genres_qs = genres_qs.exclude(genre_name__icontains='Romance')
            genres_qs = genres_qs.exclude(genre_name__icontains='Erotica')
            genres_qs = genres_qs.exclude(genre_name__icontains='Adult')
        
        if user.age is not None and user.age < 16:
            genres_qs = genres_qs.exclude(genre_name__icontains='Crime')
    genres = genres_qs.order_by('genre_name')

    preferred_genre_ids = []
    if user:
        preferred_genre_ids = set(GenrePreference.objects.filter(user=user).values_list('genre__genre_id', flat=True))

        if not preferred_genre_ids:
            preferred_genre_ids = set(genres_qs.values_list('genre_id', flat=True))

    if request.method == "POST":
        if not user:
            messages.error(request, "Please login to save preferences.")
            return redirect('users:login')

        selected_genres = request.POST.getlist('genres')
        duration_pref = request.POST.get('duration_preference', 'Any')
        languages = request.POST.getlist('languages')

        print(f"DEBUG: genre POST received: {selected_genres}")
        print(f"DEBUG: AJAX Request: {request.headers.get('x-requested-with')}")

        if not selected_genres and not GenrePreference.objects.filter(user=user).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'status': 'error', 'message': 'Please select at least one genre to save preferences!'}, status=400)
            messages.error(request, "Please select at least one genre!")
            return redirect('users:select_genres')

        with transaction.atomic():
            user.duration_preference = duration_pref
            user.language_preference = ",".join(languages)
            user.save()

            GenrePreference.objects.filter(user=user).delete()

            for g_id in selected_genres:
                if g_id and (str(g_id).isdigit()):
                    GenrePreference.objects.create(
                        user=user,
                        genre_id=int(g_id)
                    )

            from django.core.cache import cache
            cache.delete(f"user_dash_v16_{user.user_id}")
            cache.delete(f"user_dash_v15_{user.user_id}")
            cache.delete(f"user_dash_v14_{user.user_id}")
            cache.delete(f"user_dash_v10_{user.user_id}")
            cache.delete(f"user_dash_v9_{user.user_id}")
            cache.delete(f"user_dash_v8_{user.user_id}")
            cache.delete(f"user_dash_v7_{user.user_id}")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'status': 'success', 'message': 'Preferences saved!'})

        messages.success(request, "Movie preferences updated!")
        return redirect('dashboard:user_dashboard')

    from ml_models.models import Rating
    user_ratings = Rating.objects.filter(user=user).select_related('movie') if user else []

    context = {
        'user': user,
        'current_user': user,
        'genres': genres,
        'preferred_genre_ids': preferred_genre_ids,
        'duration_preference': user.duration_preference if user else 'Any',
        'preferred_languages': user.language_preference.split(',') if user and user.language_preference else ['English'],
        'full_language_list': ['English', 'Punjabi', 'Hindi', 'Japanese', 'Korean'],
        'user_ratings': user_ratings,
    }
    return render(request, 'users/profile.html', context)

def send_otp_view(request):

    return redirect('users:signup')

def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        pw = request.POST.get('password')

        try:

            user = User.objects.filter(Q(email=identifier) | Q(username=identifier)).first()

            if user:
                if check_password(pw, user.password):
                    if not user.is_verified:
                        messages.error(request, "Your email is not verified yet. Please check your inbox.")
                        return redirect('users:login')

                    if not user.is_active:
                        messages.error(request, "This account is deactivated. Please contact support to reactivate.")
                        return redirect('users:login')

                    code = str(random.randint(1000, 9999))
                    user.two_fa_code = code
                    user.otp_created_at = timezone.now()
                    user.save()

                    try:
                        send_mail(
                            'CinemaStream Login Code',
                            f'Your verification code is: {code}',
                            settings.EMAIL_HOST_USER,
                            [user.email],
                            fail_silently=False,
                        )
                    except Exception as e:
                        messages.warning(request, f"Email delivery failed: {str(e)}. Please check your internet connection.")

                    request.session['temp_user_id'] = user.user_id
                    messages.success(request, f"A verification code has been sent to {user.email}")
                    return redirect('users:verify_mock_2fa')
                else:
                    messages.error(request, "Wrong Password!")
            else:
                messages.error(request, "Identifier (Email/Username) not registered!")
        except Exception as e:
            messages.error(request, f"Login Error: {str(e)}")

    return render(request, 'users/login.html')

@login_required_custom
def delete_account_view(request):
    if request.method == "POST":
        user = request.current_user
        if user.is_admin or user.email == 'harschx31@gmail.com' or user.username == 'AdminAccount001':
            messages.error(request, "This is a root administrator account and cannot be deleted from the user dashboard.")
            return redirect('users:profile')
        user.delete()
        request.session.flush()
        messages.error(request, "Your account has been permanently deleted.")
        return redirect('core:index')
    return redirect('users:profile')

def profile_view(request):

    return select_genres_view(request)

def logout_view(request):
    request.session.flush()
    messages.info(request, "Logged out successfully.")
    return redirect('core:index')

@login_required_custom
def edit_profile_view(request):
    user = request.current_user

    if request.method == "POST":

        uname = request.POST.get('username')
        email = request.POST.get('email')

        if uname:
            if " " in uname:
                messages.error(request, "Username cannot contain spaces.")
                return redirect('users:edit_profile')
            if User.objects.filter(username=uname).exclude(user_id=user.user_id).exists():
                messages.error(request, "Username is already taken, please choose something else.")
                return redirect('users:edit_profile')

        if User.objects.filter(email=email).exclude(user_id=user.user_id).exists():
            messages.error(request, "Email already exists!")
            return redirect('users:edit_profile')

        user.username = uname
        user.email = email

        age_str = request.POST.get('age')
        user.age = int(age_str) if age_str and age_str.isdigit() else user.age

        user.gender = request.POST.get('gender')
        user.bio = request.POST.get('bio')

        if request.FILES.get('profile_pic'):
            user.profile_pic = request.FILES.get('profile_pic')

        try:
            user.save()
            from django.core.cache import cache

            cache_key = f"user_dash_v16_{user.user_id}"
            cache.delete(cache_key)
            cache.delete(f"user_dash_v13_{user.user_id}")
            cache.delete(f"user_dash_v12_{user.user_id}")
            cache.delete(f"user_dash_v11_{user.user_id}")
            cache.delete(f"user_dash_v10_{user.user_id}")
            cache.delete(f"user_dash_v9_{user.user_id}")
            cache.delete(f"user_dash_v8_{user.user_id}")
            cache.delete(f"user_dash_v7_{user.user_id}")
            messages.success(request, "Profile updated successfully!")
        except Exception as e:
            logger.exception("Error updating profile for user %s", user.user_id)
            messages.error(request, f"Error updating profile: {str(e)}")
            return redirect('users:edit_profile')
        return redirect('users:profile')

    return render(request, 'users/editprofile.html', {'current_user': user})

def helpcenter_view(request):
    return render(request, 'users/helpcenter.html')

def termsofservices_view(request):
    return render(request, 'users/termsofservice.html')

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)

            if user.is_admin or user.email == settings.BOSS_EMAIL:
                messages.error(request, "This account is under high-security lockdown. Password resets via this form are strictly prohibited.")
                return redirect('users:forgot_password')

            code = str(random.randint(100000, 999999))
            user.reset_code = code
            user.otp_created_at = timezone.now()
            user.save()

            try:
                send_mail(
                    'CinemaStream Password Reset',
                    f'Your reset code is: {code}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(request, f"Email delivery failed: {str(e)}. Please try again later.")

            request.session['reset_email'] = email
            messages.success(request, f"Reset code sent to {email}")
            return redirect('users:reset_password')
        except User.DoesNotExist:
            messages.error(request, "Email not found!")

    return render(request, 'users/forgot_password.html')

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('users:forgot_password')

    if request.method == "POST":
        code = request.POST.get('code')
        new_pw = request.POST.get('password')
        confirm_pw = request.POST.get('confirm_password')

        if new_pw != confirm_pw:
            messages.error(request, "Passwords do not match!")
            return redirect('users:reset_password')

        try:
            user = User.objects.get(email=email, reset_code=code)

            if user.otp_created_at and (timezone.now() - user.otp_created_at).total_seconds() > 300:
                messages.error(request, "Reset code has expired. Please request a new one.")
                return redirect('users:reset_password')
        except User.DoesNotExist:
            messages.error(request, "Invalid or expired reset code.")
            return redirect('users:reset_password')

        user.password = make_password(new_pw)
        user.reset_code = None
        user.otp_created_at = None
        user.password_last_updated = timezone.now()
        user.save()

        del request.session['reset_email']

        messages.success(request, "Password reset successfully! Please login.")
        return redirect('users:login')

    return render(request, 'users/reset_password.html')

def resend_reset_otp_view(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Session expired. Please start again.")
        return redirect('users:forgot_password')

    try:
        user = User.objects.get(email=email)

        code = str(random.randint(100000, 999999))
        user.reset_code = code
        user.otp_created_at = timezone.now()
        user.save()

        send_mail(
            'CinemaStream Password Reset',
            f'Your new reset code is: {code}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        messages.success(request, f"A new reset code has been sent to {email}")
    except Exception as e:
        logger.exception("Error resending reset OTP for email %s", email)
        messages.error(request, f"Error: {str(e)}")

    return redirect('users:reset_password')

@login_required_custom
def change_password_view(request):
    user = request.current_user

    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not check_password(current_password, user.password):
            messages.error(request, "Incorrect current password!")
            return redirect('users:change_password')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match!")
            return redirect('users:change_password')

        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('users:change_password')

        user.password = make_password(new_password)
        user.password_last_updated = timezone.now()
        user.save()
        messages.success(request, "Password changed successfully!")
        return redirect('core:index')

    return render(request, 'users/change_password.html')