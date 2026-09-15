from django.urls import path

from django.urls import path
from . import views

urlpatterns = [

    path("signup/",views.signup,name="photographer_signup"),
    path("login/",views.login,name="photographer_login"),
    path("profile/update/",views.profile_update,name="photographer_profile_update"),
    path("profile/",views.profile,name="photographer_profile"),
    path("verification/",views.verification,name="photographer_verification"),
    
    path("notifications/",views.photographer_notifications,name="photographer_notifications"),
    path("weekly-availability/", views.create_weekly_availability, name="create_weekly_availability"),
    path("weekly-availability/view/", views.my_weekly_availability, name="my_weekly_availability"),
    path("weekly-availability/update/<int:availability_id>/", views.update_weekly_availability, name="update_weekly_availability"),
    path("weekly-availability/delete/<int:availability_id>/", views.delete_weekly_availability, name="delete_weekly_availability"),
    path("availability-exception/", views.create_availability_exception, name="create_availability_exception"),
    path("availability-exception/view/", views.my_availability_exceptions, name="my_availability_exceptions"),
    path("availability-exception/delete/<int:exception_id>/", views.delete_availability_exception, name="delete_availability_exception"),
    path("verify-otp/",views.verify_otp,name="verify_otp"), 
    path(
    "photographer/Add-Service-charges/",
    views.create_photographer_charge,
    name="create-photographer-charge"
),
    path(
    "booking/requests/",
    views.photographer_booking_requests,
    name="photographer-booking-requests"
),
    path(
    "booking/<int:booking_id>/accept/",
    views.accept_booking_request,
    name="accept-booking-request"
),

    path(
    "booking/<int:booking_id>/reject/",
    views.reject_booking_request,
    name="reject-booking-request"
),
    path(
    "my-bookings/",
    views.photographer_my_bookings,
    name="photographer-my-bookings"
),
    path(
    "booking/<int:booking_id>/work-status/",
    views.update_work_status,
    name="update-work-status"
),
    path(
        "dashboard/",
        views.photographer_dashboard,
        name="photographer-dashboard"
    ),

    path(
    "service-charges/",
    views.view_service_charges,
    name="view-service-charges"
),


    path(
    "update-service-charges/<int:charge_id>/",
    views.update_service_charge,
    name="update-service-charge"
)


    ]
