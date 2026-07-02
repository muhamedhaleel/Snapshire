from django.urls import path

from django.urls import path
from . import views

urlpatterns = [

    path("signup/",views.signup,name="photographer_signup"),
    path("login/",views.login,name="photographer_login"),
    path("profile/update/",views.profile_update,name="photographer_profile_update"),
    path("profile/",views.profile,name="photographer_profile"),
    path("verification/",views.verification,name="photographer_verification"),


]

