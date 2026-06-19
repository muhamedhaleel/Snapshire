"""
URL configuration for snapshire project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('user.urls')),
    path('photographer/', include('photographer.urls')),
]
