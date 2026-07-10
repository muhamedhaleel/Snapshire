from django.urls import path

from django.urls import path
from . import views

urlpatterns = [

    path("signup/",views.signup,name="photographer_signup"),
    path("login/",views.login,name="photographer_login"),
    path("profile/update/",views.profile_update,name="photographer_profile_update"),
    path("profile/",views.profile,name="photographer_profile"),
    path("verification/",views.verification,name="photographer_verification"),
    path("calendar/",views.calendar_view,name="calendar"),
    path("add-availability/",views.save_availability,name="add-availability"),
    path("update-availability/<int:id>/",views.update_availability,name="update-availability"),
    path("delete-availability/<int:id>/",views.delete_availability,name="delete-availability"),
    path("my-availability/",views.my_availability,name="my-availability"),
    path("notifications/",views.photographer_notifications,name="photographer_notifications")



]
