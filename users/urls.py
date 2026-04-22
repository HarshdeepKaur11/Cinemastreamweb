

from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('verify-otp/', views.verify_signup_otp_view, name='verify_signup_otp'),
    path('resend-signup-otp/', views.resend_signup_otp_view, name='resend_signup_otp'),
    path('select_genres/', views.select_genres_view, name='select_genres'),
    path('send_otp/', views.send_otp_view, name='send_otp'),
    path('login/', views.login_view, name='login'),
    path('mock_2fa/', views.mock_2fa_view, name='mock_2fa'),
    path('verify_mock_2fa/', views.verify_mock_2fa_view, name='verify_mock_2fa'),
    path('resend-2fa-otp/', views.resend_2fa_otp_view, name='resend_2fa_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('editprofile', views.edit_profile_view, name='edit_profile'),
    path('help/',views.helpcenter_view, name='helpcenter'),
    path('termsofservice/',views.termsofservices_view, name='termsofservices'),
    path('forgot_password/', views.forgot_password_view, name='forgot_password'),
    path('reset_password/', views.reset_password_view, name='reset_password'),
    path('resend-reset-otp/', views.resend_reset_otp_view, name='resend_reset_otp'),
    path('change_password/', views.change_password_view, name='change_password'),
    path('delete/', views.delete_account_view, name='delete_account'),
    path('logout/', views.logout_view, name='logout'),
]