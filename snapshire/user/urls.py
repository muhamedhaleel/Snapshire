from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.signup, name='signup'),
]
