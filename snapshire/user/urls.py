from django.urls import path

from django.urls import path

from . import views

urlpatterns = [

    path("signup/",views.signup,name="signup"),
    path("login/",views.login,name="login"),
    path("profile/update/", views.profile_update, name="profile_update"),
    path("profile/", views.profile, name="profile"),
    path("view-photographers/",views.view_photographers,name="view-photographers"),
     
]