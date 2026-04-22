

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.learn_more_view, name='learnmore'),
    path('security/', views.security_view, name='security'),
    path('setting/', views.setting_view, name='setting'),
    path('search/', views.search_view, name='search'),
    path('api/toggle-genre/', views.toggle_genre_preference, name='toggle_genre'),
    path('security/verify-email/', views.verify_email_change_view, name='verify_email_change'),
    path('security/resend-email-otp/', views.resend_email_change_otp_view, name='resend_email_change_otp'),
    path('faq/', views.faq_view, name='faq'),
]