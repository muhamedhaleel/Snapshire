from django.contrib import admin

from .models import PhotographerProfile, PortfolioFile, PortfolioLink


class PortfolioLinkInline(admin.TabularInline):
    model = PortfolioLink
    extra = 0


class PortfolioFileInline(admin.TabularInline):
    model = PortfolioFile
    extra = 0
    readonly_fields = ('original_name', 'created_at')


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'location', 'plan_mode', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'specialty', 'location')
    inlines = [PortfolioLinkInline, PortfolioFileInline]


@admin.register(PortfolioLink)
class PortfolioLinkAdmin(admin.ModelAdmin):
    list_display = ('profile', 'url', 'created_at')
    search_fields = ('url', 'profile__user__username')


@admin.register(PortfolioFile)
class PortfolioFileAdmin(admin.ModelAdmin):
    list_display = ('profile', 'original_name', 'created_at')
    search_fields = ('original_name', 'profile__user__username')
