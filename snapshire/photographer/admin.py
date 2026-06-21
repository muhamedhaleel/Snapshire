from django.contrib import admin

from .models import PhotographerProfile, PortfolioLink


class PortfolioLinkInline(admin.TabularInline):
    model = PortfolioLink
    extra = 0


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'location', 'plan_mode', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'specialty', 'location')
    inlines = [PortfolioLinkInline]


@admin.register(PortfolioLink)
class PortfolioLinkAdmin(admin.ModelAdmin):
    list_display = ('profile', 'url', 'created_at')
    search_fields = ('url', 'profile__user__username')
