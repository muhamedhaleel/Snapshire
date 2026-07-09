from django.urls import path

from django.urls import path

from . import views

urlpatterns = [

    path("signup/",views.signup,name="signup"),
    path("login/",views.login,name="login"),
    path("profile/update/", views.profile_update, name="profile_update"),
    path("profile/", views.profile, name="profile"),
    path("view-photographers/",views.view_photographers,name="view-photographers"),
    path("Detail-photographers/<int:id>/",views.photographer_detail,name="photographer-detail"),
    path("Availibility-photographers/<int:photographer_id>/availability/",views.photographer_availability,name="photographer-availability"),
    path("bookings/",views.create_booking,name="create-booking"),
    path(
        "bookings/status/",
        views.user_booking_status,
        name="user-booking-status",
    ),
     
]