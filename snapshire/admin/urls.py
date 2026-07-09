from django.urls import path

from . import views

urlpatterns = [
    path("login/",views.admin_login,name="admin_login"),
     path(
        "users/",
        views.user_list,
        name="user_list"
    ),

    path(
        "users/<int:user_id>/block/",
        views.block_user,
        name="block_user"
    ),

    path(
        "users/<int:user_id>/unblock/",
        views.unblock_user,
        name="unblock_user"
    ),
    path(
        "photographers/",
        views.photographer_list,
        name="photographer_list"
    ),

    path(
        "photographers/<int:photographer_id>/block/",
        views.block_photographer,
        name="block_photographer"
    ),

    path(
        "photographers/<int:photographer_id>/unblock/",
        views.unblock_photographer,
        name="unblock_photographer"
    ),

    path(
        "photographers/<int:photographer_id>/verify/",
        views.verify_photographer,
        name="verify_photographer"
    ),

    path(
    "booking-management/",
    views.admin_booking_management,
    name="admin-booking-management",
),

    

]