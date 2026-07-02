# """
# URL configuration for snapshire project.
# """
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import include, path

# urlpatterns = [
#     path('django-admin/', admin.site.urls),
#     path('admin/', include('admin.urls')),
#     path('', include('user.urls')),
#     path('photographer/', include('photographer.urls')),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import include, path

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
    openapi.Info(
        title="SnapHire API",
        default_version="v1",
        description="SnapHire Backend APIs",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [

    path('django-admin/', admin.site.urls),

    path('api/user/', include('user.urls')),

    path('api/photographer/', include('photographer.urls')),

    path('api/admin/', include('admin.urls')),

    path(
        'swagger/',
        schema_view.with_ui('swagger', cache_timeout=0),
        name='swagger'
    ),

    path(
        'redoc/',
        schema_view.with_ui('redoc', cache_timeout=0),
        name='redoc'
    ),
]