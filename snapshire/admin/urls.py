from django.urls import path

from . import views

urlpatterns = [
    path('', views.admin_home, name='admin_home'),
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('users/', views.admin_user_list, name='admin_user_list'),
    path('users/<int:user_id>/toggle-block/', views.admin_toggle_user_block, name='admin_toggle_user_block'),
    path('photographers/', views.admin_photographer_list, name='admin_photographer_list'),
    path('photographers/<int:user_id>/toggle-block/', views.admin_toggle_photographer_block, name='admin_toggle_photographer_block'),
]
