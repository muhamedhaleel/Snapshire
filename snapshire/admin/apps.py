from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin'
    label = 'snapshire_admin'
    verbose_name = 'Snapshire Admin Panel'
