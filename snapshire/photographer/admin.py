from django.contrib import admin

from .models import PhotographerProfile


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'location', 'plan_mode', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'specialty', 'location')
