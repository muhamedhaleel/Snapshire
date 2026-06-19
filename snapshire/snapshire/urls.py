"""
URL configuration for snapshire project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', include('admin.urls')),
    path('', include('user.urls')),
    path('photographer/', include('photographer.urls')),
]
