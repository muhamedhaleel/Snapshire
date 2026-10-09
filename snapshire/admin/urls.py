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
    path(
    "photographers/verification-pending/",
    views.pending_photographers,
    name="pending-photographers",
    ),
    path(
    "photographers/search/",
    views.search_photographers,
    name="search-photographers",
),
    path(
    "users/search/",
    views.search_users,
    name="search-users"
),
   
    path(
        "platform-fee/",
        views.set_platform_fee,
        name="set-platform-fee"
    ),
    path(
        "dashboard/",
        views.admin_dashboard,
        name="admin-dashboard"
    ),
    path(
    "User_feedback/",
    views.admin_feedback_list,
    name="admin-feedback-list"
),

    path(
        "wallet/",
        views.admin_wallet,
        name="admin-wallet"
    ),

    path(
        "admin/cancelled-bookings/",
        views.admin_cancelled_bookings,
        name="admin-cancelled-bookings"
    ),

    path(
        "photographer-transactions-details/",
        views.admin_photographer_transactions,
        name="admin-photographer-transactions"
),
    path(
    "user-refund-transactions-details/",
    views.admin_user_refund_transactions,
    name="admin-user-refund-transactions"
),   

    path(
        "verification-plans/",
        views.add_verification_plan,
        name="add-verification-plan",
    ),
    path(
        "verification-plans/list/",
        views.list_verification_plans,
        name="list-verification-plans",
    ),
    path(
        "verification-plans-update/<int:plan_id>/",
        views.update_verification_plan,
        name="update-verification-plan",
    ),



    

]