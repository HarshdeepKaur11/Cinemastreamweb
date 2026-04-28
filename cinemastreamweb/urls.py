

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('core.urls')),              # homepage only here

    path('dashboard/', include('dashboard.urls')),

    path('users/', include('users.urls')),

    path('admin_panel/', include('admin_panel.urls')),
]