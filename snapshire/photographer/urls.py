from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.photographer_home, name='photographer_home'),
    path('profile/edit/', views.photographer_edit_profile, name='photographer_edit_profile'),
    path('verification/', views.photographer_verification, name='photographer_verification'),
    path('login/', views.photographer_login, name='photographer_login'),
    path('logout/', views.photographer_logout, name='photographer_logout'),
    path('signup/', views.photographer_signup, name='photographer_signup'),
]
