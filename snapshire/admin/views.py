from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Q
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import AdminRevenueReportsSerializer
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Sum, Count, Q, Case, When, F, DecimalField, Value
from user.models import UserProfile,Booking,Feedback,Payment,WalletTransaction,RescheduleRequest
from photographer.models import PhotographerProfile,VerificationPayment
from .serializers import PendingPhotographerSerializer,AdminDashboardSerializer,AdminPhotographerFeedbackSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from .models import PlatformFee,VerificationPlan
from datetime import datetime
from django.utils import timezone
from .models import ActivityLog
from .serializers import ActivityLogSerializer

from django.db.models.functions import TruncMonth
from .serializers import (
    AdminLoginSerializer,
    UserListSerializer,
    PhotographerListSerializer,
    AdminBookingManagementSerializer,PlatformFeeSerializer,
    AdminFeedbackSerializer,AdminWalletTransactionSerializer,
    AdminCancelledBookingSerializer,AdminPhotographerTransactionSerializer,
    PhotographerWalletTransaction,AdminUserRefundTransactionSerializer,PremiumVerificationSerializer,
    AdminWalletTransactionSerializer,
    AdminVerificationWalletTransactionSerializer,
    AdminRescheduleRequestSerializer
)
from .serializers import VerificationPlanSerializer,AdminPhotographerReportsSerializer,PhotographerPerformanceSerializer,UserReportItemSerializer
from photographer.models import VerificationPayment



# ===========================
# Admin Login
# ===========================

@swagger_auto_schema(
    method="post",
    request_body=AdminLoginSerializer,
    responses={200: "Admin Login Successful"},
)
@api_view(["POST"])
@parser_classes([FormParser])
def admin_login(request):

    serializer = AdminLoginSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Admin Login Successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===========================
# User List
# ===========================

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ]
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_list(request):

    users = UserProfile.objects.select_related("user").order_by("-created_at")
    paginator = PageNumberPagination()
    paginator.page_size = 1
    result_page = paginator.paginate_queryset(
        users,
        request
    )

    serializer = UserListSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)

# ===========================
# Block User
# ===========================

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def block_user(request, user_id):

    try:
        profile = UserProfile.objects.select_related("user").get(
            user__id=user_id
        )

    except UserProfile.DoesNotExist:

        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.user.is_active = False
    profile.user.save()

    return Response(
    {
        "message": f"User '{profile.user.username}' has been blocked successfully.",
        "username": profile.user.username,
        "status": "Blocked"
    },
    status=status.HTTP_200_OK
)


# ===========================
# Unblock User
# ===========================

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def unblock_user(request, user_id):

    try:
        profile = UserProfile.objects.select_related("user").get(
            user__id=user_id
        )

    except UserProfile.DoesNotExist:

        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.user.is_active = True
    profile.user.save()

    return Response(
    {
        "message": f"User '{profile.user.username}' has been unblocked successfully.",
        "username": profile.user.username,
        "status": "Active"
    },
    status=status.HTTP_200_OK
)

# ===========================
# Photographer List
# ===========================

# @swagger_auto_schema(
#     method="get",
#     responses={200: PhotographerListSerializer(many=True)},
# )
# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def photographer_list(request):

#     photographers = PhotographerProfile.objects.select_related("user")
#     paginator = PageNumberPagination()
#     paginator.page_size = 2


#     result_page = paginator.paginate_queryset(
#         photographers,
#         request
#     )

#     serializer = PhotographerListSerializer(
#         photographers,
#         many=True,
#     )

#     return paginator.get_paginated_response(
#         serializer.data
#     )

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        # openapi.Parameter(
        #     "page_size",
        #     openapi.IN_QUERY,
        #     description="Number of photographers per page",
        #     type=openapi.TYPE_INTEGER,
        #     required=False,
        # ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def photographer_list(request):

    photographers = PhotographerProfile.objects.select_related(
        "user"
    ).order_by("-created_at")

    paginator = PageNumberPagination()
    paginator.page_size = 3
    result_page = paginator.paginate_queryset(
        photographers,
        request
    )

    serializer = PhotographerListSerializer(
        result_page,
        many=True
    )

    return paginator.get_paginated_response(
        serializer.data
    )


# ===========================
# Block Photographer
# ===========================

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def block_photographer(request, photographer_id):

    try:
        profile = PhotographerProfile.objects.select_related("user").get(
            user__id=photographer_id
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.user.is_active = False
    profile.user.save()

    return Response(
    {
        "message": f"Photographer '{profile.user.username}' has been blocked successfully.",
        "username": profile.user.username,
        "status": "Blocked"
    },
    status=status.HTTP_200_OK
)

# ===========================
# Unblock Photographer
# ===========================

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def unblock_photographer(request, photographer_id):

    try:
        profile = PhotographerProfile.objects.select_related("user").get(
            user__id=photographer_id
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.user.is_active = True
    profile.user.save()

    return Response(
    {
        "message": f"Photographer '{profile.user.username}' has been unblocked successfully.",
        "username": profile.user.username,
        "status": "Active"
    },
    status=status.HTTP_200_OK
)


# ===========================
# Verify Photographer
# ===========================

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def verify_photographer(request, photographer_id):

    try:
        profile = PhotographerProfile.objects.select_related("user").get(
            user__id=photographer_id
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    profile.is_verified = True
    profile.verification_status = "Approved"
    profile.save()

    return Response( 
        
       {
        "message": f"Photographer '{profile.user.username}' has been verified successfully.",
        "username": profile.user.username,
        "verification_status": profile.verification_status,
        "is_verified": profile.is_verified,
    },
    status=status.HTTP_200_OK,
)
   

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Page number",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
    
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_booking_management(request):

    bookings = Booking.objects.select_related(
        "user",
        "photographer",
        "photographer__user"
    ).order_by("-created_at")

    paginator = PageNumberPagination()
    paginator.page_size = 3
    result_page = paginator.paginate_queryset(
        bookings,
        request
    )

    serializer = AdminBookingManagementSerializer(
        result_page,
        many=True
    )

    return paginator.get_paginated_response(
        serializer.data
    )

@api_view(["GET"])
@permission_classes([IsAdminUser])
def pending_photographers(request):

    photographers = PhotographerProfile.objects.filter(
        verification_status="Pending"
    ).order_by("-created_at")

    serializer = PendingPhotographerSerializer(
        photographers,
        many=True
    )

    return Response(serializer.data)


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi



@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="search",
            in_=openapi.IN_QUERY,
            description="Search photographer by first name, last name, username, or email",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def search_photographers(request):

    search = request.GET.get("search", "").strip()

    if not search:
        return Response(
            {
                "success": False,
                "message": "Please enter a name, username, or email."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    photographers = PhotographerProfile.objects.filter(
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search) |
        Q(user__username__icontains=search) |
        Q(user__email__icontains=search)
    ).select_related("user")

    serializer = PhotographerListSerializer(
        photographers,
        many=True
    )

    return Response(
        {
            "success": True,
            "message": "Photographers retrieved successfully.",
            "count": photographers.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="search",
            in_=openapi.IN_QUERY,
            description="Search user by username, first name, last name, or email",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def search_users(request):

    search = request.GET.get("search", "").strip()

    if not search:
        return Response(
            {
                "success": False,
                "message": "Please enter a username, name, or email."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    users = UserProfile.objects.select_related("user").filter(
        Q(user__username__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search) |
        Q(user__email__icontains=search)
    )

    if not users.exists():
        return Response(
            {
                "success": False,
                "message": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UserListSerializer(
        users,
        many=True
    )

    return Response(
        {
            "success": True,
            "message": "Users retrieved successfully.",
            "count": users.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="post",
    request_body=PlatformFeeSerializer
)
@api_view(["POST"])
@permission_classes([IsAdminUser])
@parser_classes([FormParser])
def set_platform_fee(request):

    fee = PlatformFee.objects.first()

    if fee:
        serializer = PlatformFeeSerializer(
            fee,
            data=request.data,
            partial=True
        )
    else:
        serializer = PlatformFeeSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            {
                "success": True,
                "message": "Platform fee updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    return Response(
        {
            "success": False,
            "errors": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="get",
    responses={200: AdminDashboardSerializer},
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_dashboard(request):

    # 1. Existing overview metrics
    total_users = User.objects.count()
    total_photographers = PhotographerProfile.objects.count()
    total_bookings = Booking.objects.count()

    total_verified_photographers = (
        PhotographerProfile.objects.filter(is_verified=True).count()
    )

    total_gold_photographers = (
        PhotographerProfile.objects.filter(plan_mode="gold").count()
    )

    total_platinum_photographers = (
        PhotographerProfile.objects.filter(plan_mode="platinum").count()
    )

    # 2. Booking status summary: only statuses with existing bookings
    booking_status = {
        item["status"]: item["count"]
        for item in Booking.objects.values("status").annotate(
            count=Count("id")
        )
    }

    # 3. Successful booking payments
    paid_payments = Payment.objects.filter(status="paid")

    payment_totals = paid_payments.aggregate(
        total_collected=Sum("amount"),
        advance_collected=Sum(
            "amount",
            filter=Q(payment_type="advance"),
        ),
        balance_collected=Sum(
            "amount",
            filter=Q(payment_type="balance"),
        ),
    )

    total_collected = (
        payment_totals["total_collected"] or Decimal("0.00")
    )
    advance_collected = (
        payment_totals["advance_collected"] or Decimal("0.00")
    )
    balance_collected = (
        payment_totals["balance_collected"] or Decimal("0.00")
    )

    failed_payment_count = Payment.objects.filter(
        status="failed"
    ).count()

    # 4. Subscription overview
    # Counts are available from PhotographerProfile.
    # Actual subscription revenue requires subscription-payment records.
    subscription_revenue = {
        "gold": Decimal("0.00"),
        "platinum": Decimal("0.00"),
        "total": Decimal("0.00"),
    }

    # 5. Admin action counts
    bookings_waiting_admin = Booking.objects.filter(
        status="waiting_admin"
    ).count()

    photographers_awaiting_verification = (
        PhotographerProfile.objects.filter(is_verified=False).count()
    )

    # 6. Response data
    data = {
        # Existing fields
        "total_users": total_users,
        "total_photographers": total_photographers,
        "total_bookings": total_bookings,
        "total_verified_photographers": total_verified_photographers,
        "total_gold_photographers": total_gold_photographers,
        "total_platinum_photographers": total_platinum_photographers,

        # Booking analytics
        "booking_status": booking_status,

        # Booking-payment analytics
        "total_collected": total_collected,
        "advance_collected": advance_collected,
        "balance_collected": balance_collected,
        "failed_payment_count": failed_payment_count,

        # Subscription analytics
        "subscription_revenue": subscription_revenue,

        # Admin actions
        "bookings_waiting_admin": bookings_waiting_admin,
        "photographers_awaiting_verification":
            photographers_awaiting_verification,
    }

    serializer = AdminDashboardSerializer(data)

    return Response(
        {
            "success": True,
            "message": "Admin dashboard data retrieved successfully.",
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

@swagger_auto_schema(
    method="get",
    manual_parameters=[

        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Enter page number",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_feedback_list(request):

    feedbacks = Feedback.objects.select_related(
        "user",
        "booking",
        "photographer",
        "photographer__user"
    ).order_by("-created_at")

    paginator = PageNumberPagination()
    paginator.page_size = 10

    paginated_feedbacks = paginator.paginate_queryset(
        feedbacks,
        request,
    )

    serializer = AdminFeedbackSerializer(
        paginated_feedbacks,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "page_size": 10,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


from decimal import Decimal

from django.db.models import Sum

from rest_framework.decorators import (
    api_view,
    permission_classes
)
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema


# @swagger_auto_schema(
#     method="get",
#     responses={
#         200: AdminWalletTransactionSerializer(many=True)
#     }
# )
# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def admin_wallet(request):

#     # -----------------------------------------
#     # PAID ADVANCE PAYMENTS ONLY
#     # -----------------------------------------

#     payments = Payment.objects.filter(
#         payment_type="advance",
#         status="paid",
#         booking__platform_fee__gt=0
#     ).select_related(
#         "booking",
#         "booking__user",
#         "booking__photographer",
#         "booking__photographer__user"
#     ).order_by("-created_at")

#     # -----------------------------------------
#     # ADMIN WALLET
#     # ONLY PLATFORM FEES
#     # -----------------------------------------

#     total_balance = (
#         payments.aggregate(
#             total=Sum("booking__platform_fee")
#         )["total"]
#         or Decimal("0.00")
#     )

#     # -----------------------------------------
#     # SERIALIZE TRANSACTIONS
#     # -----------------------------------------

#     serializer = AdminWalletTransactionSerializer(
#         payments,
#         many=True
#     )

#     # -----------------------------------------
#     # RESPONSE
#     # -----------------------------------------

#     return Response(
#         {
#             "success": True,
#             "message": "Admin wallet retrieved successfully.",

#             "data": {
#                 "total_balance": str(total_balance),

#                 "transactions": serializer.data
#             }
#         },
#         status=status.HTTP_200_OK
#     )

# @swagger_auto_schema(
#     method="get",
#     manual_parameters=[
#         openapi.Parameter(
#             name="page",
#             in_=openapi.IN_QUERY,
#             description="Enter the page number",
#             type=openapi.TYPE_INTEGER,
#             required=False,
#         ),
        
#     ]
# )
# @api_view(["GET"])
# @permission_classes([IsAdminUser])
# def admin_wallet(request):

#     # 1. Booking platform fee transactions
#     booking_payments = Payment.objects.filter(
#         payment_type="advance",
#         status="paid",
#         booking__platform_fee__gt=0
#     ).select_related(
#         "booking",
#         "booking__user",
#         "booking__photographer",
#         "booking__photographer__user"
#     ).order_by("-created_at")

#     booking_transactions = []
#     booking_total = Decimal("0.00")
#     processed_booking_ids = set()

#     for payment in booking_payments:
#         booking = payment.booking

#         # Avoid counting a booking fee more than once
#         if booking.id in processed_booking_ids:
#             continue

#         processed_booking_ids.add(booking.id)
#         booking_total += booking.platform_fee

#         transaction = dict(
#             AdminWalletTransactionSerializer(payment).data
#         )
#         transaction["transaction_type"] = "booking_platform_fee"
#         transaction["wallet_credit"] = str(booking.platform_fee)
#         booking_transactions.append(transaction)

#     # 2. Gold and Platinum verification transactions
#     verification_payments = VerificationPayment.objects.filter(
#         plan_mode__in=["gold", "platinum"],
#         status="paid"
#     ).select_related(
#         "photographer",
#         "photographer__user"
#     ).order_by("-created_at")

#     verification_total = (
#         verification_payments.aggregate(
#             total=Sum("amount")
#         )["total"] or Decimal("0.00")
#     )

#     verification_transactions = []

#     for payment in verification_payments:
#         transaction = dict(
#             AdminVerificationWalletTransactionSerializer(payment).data
#         )
#         transaction["transaction_type"] = "premium_verification"
#         transaction["wallet_credit"] = str(payment.amount)
#         verification_transactions.append(transaction)

#     # 3. Combine and sort transactions
#     transactions = booking_transactions + verification_transactions
#     transactions.sort(
#         key=lambda item: item.get("created_at") or "",
#         reverse=True
#     )

#     # 4. Pagination
#     paginator = PageNumberPagination()
#     paginator.page_size = 10
#     paginator.page_size_query_param = "page_size"
#     paginator.max_page_size = 100

#     paginated_transactions = paginator.paginate_queryset(
#         transactions, request
#     )

#     # 5. Combined totals
#     total_balance = booking_total + verification_total

#     return Response(
#         {
#             "success": True,
#             "message": "Admin wallet retrieved successfully.",
#             "data": {
#                 "total_balance": str(total_balance),
#                 "booking_platform_fee_total": str(booking_total),
#                 "premium_verification_total": str(verification_total),
#                 "transactions_count": len(transactions),
#                 "count": paginator.page.paginator.count,
#                 "total_pages": paginator.page.paginator.num_pages,
#                 "current_page": paginator.page.number,
#                 "next": paginator.get_next_link(),
#                 "previous": paginator.get_previous_link(),
#                 "transactions": paginated_transactions,
#             },
#         },
#         status=status.HTTP_200_OK,
#     )



from decimal import Decimal

from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema




@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_wallet(request):
    # Booking platform-fee transactions
    booking_payments = Payment.objects.filter(
        payment_type="advance",
        status__in=["paid", "refunded"],
        booking__platform_fee__gt=0,
    ).select_related(
        "booking",
        "booking__user",
        "booking__photographer",
        "booking__photographer__user",
    ).order_by("-created_at")

    booking_transactions = []
    booking_total = Decimal("0.00")
    processed_booking_ids = set()

    for payment in booking_payments:
        booking = payment.booking

        # Count a booking's platform fee only once
        if booking.id in processed_booking_ids:
            continue

        processed_booking_ids.add(booking.id)

        platform_fee = booking.platform_fee
        booking_total += platform_fee

        transaction = dict(
            AdminWalletTransactionSerializer(payment).data
        )
        transaction["transaction_type"] = "booking_platform_fee"
        transaction["wallet_credit"] = str(platform_fee)

        booking_transactions.append(transaction)

    # Premium-verification transactions
    verification_payments = VerificationPayment.objects.filter(
        plan_mode__in=["gold", "platinum"],
        status="paid",
    ).select_related(
        "photographer",
        "photographer__user",
    ).order_by("-created_at")

    verification_total = (
        verification_payments.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    verification_transactions = []

    for payment in verification_payments:
        transaction = dict(
            AdminVerificationWalletTransactionSerializer(payment).data
        )
        transaction["transaction_type"] = "premium_verification"
        transaction["wallet_credit"] = str(payment.amount)

        verification_transactions.append(transaction)

    # Combine and sort transactions
    transactions = booking_transactions + verification_transactions
    transactions.sort(
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    # Pagination
    paginator = PageNumberPagination()
    paginator.page_size = 10
    paginator.page_size_query_param = "page_size"
    paginator.max_page_size = 100

    paginated_transactions = paginator.paginate_queryset(
        transactions,
        request,
    )

    total_balance = booking_total + verification_total

    return Response(
        {
            "success": True,
            "message": "Admin wallet retrieved successfully.",
            "data": {
                "total_balance": str(total_balance),
                "booking_platform_fee_total": str(booking_total),
                "premium_verification_total": str(verification_total),
                "transactions_count": len(transactions),
                "count": paginator.page.paginator.count,
                "total_pages": paginator.page.paginator.num_pages,
                "current_page": paginator.page.number,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "transactions": paginated_transactions,
            },
        },
        status=status.HTTP_200_OK,
    )









class AdminCancelledBookingPagination(PageNumberPagination):

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50



@swagger_auto_schema(
    method="get",
    responses={
        200: AdminCancelledBookingSerializer(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_cancelled_bookings(request):

    # ---------------------------------------------
    # Admin check
    # ---------------------------------------------

    if not request.user.is_staff:
        return Response(
            {
                "success": False,
                "message": "Admin access required."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    # ---------------------------------------------
    # Get cancelled bookings
    # ---------------------------------------------

    bookings = Booking.objects.filter(
        status="cancelled"
    ).select_related(
        "user",
        "photographer",
        "photographer__user"
    ).order_by(
        "-created_at"
    )

    # ---------------------------------------------
    # Pagination
    # ---------------------------------------------

    paginator = AdminCancelledBookingPagination()

    page = paginator.paginate_queryset(
        bookings,
        request
    )

    serializer = AdminCancelledBookingSerializer(
        page,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": bookings.count(),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={200: AdminPhotographerTransactionSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_photographer_transactions(request):

    transactions = PhotographerWalletTransaction.objects.select_related(
        "photographer__user",
        "booking",
        "wallet"
    ).order_by("-created_at")

    serializer = AdminPhotographerTransactionSerializer(
        transactions,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": transactions.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={
        200: AdminUserRefundTransactionSerializer(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_user_refund_transactions(request):

    transactions = WalletTransaction.objects.filter(
        transaction_type="refund"
    ).select_related(
        "user",
        "wallet",
        "booking__user",
        "booking__photographer__user",
        "payment"
    ).order_by("-created_at")

    serializer = AdminUserRefundTransactionSerializer(
        transactions,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": transactions.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method="post",
    request_body=VerificationPlanSerializer,
)
@api_view(["POST"])
@parser_classes([FormParser])
@permission_classes([IsAdminUser])
def add_verification_plan(request):
    serializer = VerificationPlanSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            {
                "message": "Verification plan created successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )


@swagger_auto_schema(
    method="get",
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_verification_plans(request):
    plans = VerificationPlan.objects.all().order_by("id")
    serializer = VerificationPlanSerializer(plans, many=True)

    return Response(
        {"data": serializer.data},
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="patch",
    request_body=VerificationPlanSerializer,
)
@api_view(["PATCH"])
@parser_classes([FormParser])
@permission_classes([IsAdminUser])
def update_verification_plan(request, plan_id):
    try:
        plan = VerificationPlan.objects.get(id=plan_id)
    except VerificationPlan.DoesNotExist:
        return Response(
            {"error": "Verification plan not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = VerificationPlanSerializer(
        plan,
        data=request.data,
        partial=True,
    )

    if serializer.is_valid():
        serializer.save()

        return Response(
            {
                "message": "Verification charge updated successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST,
    )




@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="page",
            in_=openapi.IN_QUERY,
            description="Enter page number",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def premium_verified_photographers(request):

    if not request.user.is_staff:
        return Response(
            {
                "success": False,
                "message": "You do not have permission to access this data."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    payments = VerificationPayment.objects.filter(
        plan_mode__in=["gold", "platinum"],
        status="paid"
    ).select_related(
        "photographer__user"
    ).order_by("-created_at")

    paginator = PageNumberPagination()
    paginator.page_size = 5

    paginated_payments = paginator.paginate_queryset(
        payments,
        request
    )

    serializer = PremiumVerificationSerializer(
        paginated_payments,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method="get",
    responses={200: AdminRescheduleRequestSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_view_reschedule_requests(request):

    requests = RescheduleRequest.objects.select_related(
        "user",
        "photographer",
        "photographer__user"
    ).order_by("-created_at")

    serializer = AdminRescheduleRequestSerializer(
        requests,
        many=True
    )

    return Response(
        {
            "success": True,
            "message": "Reschedule requests retrieved successfully.",
            "count": requests.count(),
            "data": serializer.data,
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Enter page number",
            type=openapi.TYPE_INTEGER,
            required=False,
        ),
        
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def photographer_feedback_for_bookings(request):

    # Get all feedback, newest first
    feedbacks = Feedback.objects.select_related(
        "user",
        "photographer",
        "booking",
    ).all().order_by("-created_at")

    # Filter by rating
    rating = request.query_params.get("rating")

    if rating:
        try:
            rating = int(rating)
        except ValueError:
            return Response(
                {
                    "success": False,
                    "message": "Rating must be an integer between 1 and 5.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if rating < 1 or rating > 5:
            return Response(
                {
                    "success": False,
                    "message": "Rating must be between 1 and 5.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedbacks = feedbacks.filter(rating=rating)

    # Filter by feedback author
    feedback_by = request.query_params.get("feedback_by")

    if feedback_by:
        if feedback_by not in ["user", "photographer"]:
            return Response(
                {
                    "success": False,
                    "message": "feedback_by must be 'user' or 'photographer'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedbacks = feedbacks.filter(feedback_by=feedback_by)

    # Filter by booking ID
    booking_id = request.query_params.get("booking_id")

    if booking_id:
        try:
            booking_id = int(booking_id)
        except ValueError:
            return Response(
                {
                    "success": False,
                    "message": "booking_id must be an integer.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        feedbacks = feedbacks.filter(booking_id=booking_id)

    paginator = PageNumberPagination()
    paginator.page_size = 10

    paginated_feedbacks = paginator.paginate_queryset(
        feedbacks,
        request,
    )

    # Serialize feedback records
    serializer = AdminPhotographerFeedbackSerializer(
        paginated_feedbacks,
        many=True,
    )

    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "page_size": 10,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

ZERO = Decimal("0.00")


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "start_date",
            openapi.IN_QUERY,
            description="Start date in YYYY-MM-DD format",
            type=openapi.TYPE_STRING,
            format="date",
            required=False,
        ),
        openapi.Parameter(
            "end_date",
            openapi.IN_QUERY,
            description="End date in YYYY-MM-DD format",
            type=openapi.TYPE_STRING,
            format="date",
            required=False,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_revenue_reports(request):
    # 1. Validate date parameters
    try:
        start_date = (
            datetime.strptime(
                request.query_params["start_date"], "%Y-%m-%d"
            ).date()
            if request.query_params.get("start_date")
            else None
        )

        end_date = (
            datetime.strptime(
                request.query_params["end_date"], "%Y-%m-%d"
            ).date()
            if request.query_params.get("end_date")
            else None
        )

    except ValueError:
        return Response(
            {
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD format.",
                "data": None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if start_date and end_date and start_date > end_date:
        return Response(
            {
                "success": False,
                "message": "start_date cannot be later than end_date.",
                "data": None,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Filter booking payments
    payments = Payment.objects.all()

    if start_date:
        payments = payments.filter(created_at__date__gte=start_date)

    if end_date:
        payments = payments.filter(created_at__date__lte=end_date)

    # 3. Count booking payments by status
    paid_payment_count = payments.filter(status="paid").count()
    failed_payment_count = payments.filter(status="failed").count()
    pending_payment_count = payments.filter(status="created").count()

    # Only paid booking payments count as collected
    paid_payments = payments.filter(status="paid")

    # 4. Calculate booking revenue totals
    booking_totals = paid_payments.aggregate(
        total=Sum("amount"),
        advance=Sum(
            "amount",
            filter=Q(payment_type="advance"),
        ),
        balance=Sum(
            "amount",
            filter=Q(payment_type="balance"),
        ),
    )

    total_collected = booking_totals["total"] or ZERO
    advance_collected = booking_totals["advance"] or ZERO
    balance_collected = booking_totals["balance"] or ZERO

    # 5. Calculate monthly booking revenue
    # Group first by month and payment type, then combine the rows.
    monthly_rows = (
        paid_payments
        .annotate(month_date=TruncMonth("created_at"))
        .values("month_date", "payment_type")
        .annotate(payment_total=Sum("amount"))
        .order_by("month_date")
    )

    monthly_data = {}

    for row in monthly_rows:
        month_date = row["month_date"]
        month_key = month_date.strftime("%b %Y")

        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "month": month_key,
                "amount": ZERO,
                "advance_amount": ZERO,
                "balance_amount": ZERO,
            }

        payment_amount = row["payment_total"] or ZERO

        monthly_data[month_key]["amount"] += payment_amount

        if row["payment_type"] == "advance":
            monthly_data[month_key]["advance_amount"] += payment_amount
        elif row["payment_type"] == "balance":
            monthly_data[month_key]["balance_amount"] += payment_amount

    monthly_revenue = list(monthly_data.values())

    # 6. Filter subscription payments by date
    subscription_payments = VerificationPayment.objects.filter(
        status="paid"
    )

    if start_date:
        subscription_payments = subscription_payments.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        subscription_payments = subscription_payments.filter(
            created_at__date__lte=end_date
        )

    # 7. Calculate Gold and Platinum subscription revenue
    subscription_totals = subscription_payments.aggregate(
        gold=Sum("amount", filter=Q(plan_mode="gold")),
        platinum=Sum("amount", filter=Q(plan_mode="platinum")),
    )

    gold_subscription_revenue = subscription_totals["gold"] or ZERO
    platinum_subscription_revenue = subscription_totals["platinum"] or ZERO

    total_subscription_revenue = (
        gold_subscription_revenue + platinum_subscription_revenue
    )

    # 8. Calculate overall collections
    overall_collected = total_collected + total_subscription_revenue

    # 9. Prepare response data
    data = {
        "start_date": start_date,
        "end_date": end_date,

        # Booking revenue
        "total_collected": total_collected,
        "advance_collected": advance_collected,
        "balance_collected": balance_collected,
        "paid_payment_count": paid_payment_count,
        "failed_payment_count": failed_payment_count,
        "pending_payment_count": pending_payment_count,
        "monthly_revenue": monthly_revenue,

        # Subscription revenue
        "gold_subscription_revenue": gold_subscription_revenue,
        "platinum_subscription_revenue": platinum_subscription_revenue,
        "total_subscription_revenue": total_subscription_revenue,

        # Combined collections
        "overall_collected": overall_collected,
    }

    serializer = AdminRevenueReportsSerializer(data)

    return Response(
        {
            "success": True,
            "message": "Revenue reports retrieved successfully.",
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )



@swagger_auto_schema(
    method="get",
    responses={200: AdminPhotographerReportsSerializer},
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_photographer_reports(request):

    # 1. Photographer overview
    photographers = PhotographerProfile.objects.all()

    total_photographers = photographers.count()

    verified_photographers = photographers.filter(
        is_verified=True
    ).count()

    unverified_photographers = photographers.filter(
        is_verified=False
    ).count()

    # 2. Gold and Platinum membership counts
    gold_photographers = photographers.filter(
        plan_mode="gold"
    ).count()

    platinum_photographers = photographers.filter(
        plan_mode="platinum"
    ).count()

    # 3. Overall booking performance
    total_bookings = Booking.objects.count()

    completed_bookings = Booking.objects.filter(
        status="completed"
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status="cancelled"
    ).count()

    # 4. Performance for each photographer
    photographer_performance = (
        photographers
        .annotate(
            total_bookings=Count("bookings", distinct=True),
            completed_bookings=Count(
                "bookings",
                filter=Q(bookings__status="completed"),
                distinct=True,
            ),
            cancelled_bookings=Count(
                "bookings",
                filter=Q(bookings__status="cancelled"),
                distinct=True,
            ),
        )
        .order_by("-total_bookings", "id")
    )

    performance_data = [
        {
            "photographer_id": photographer.id,
            "username": photographer.user.username,
            "is_verified": photographer.is_verified,
            "plan_mode": photographer.plan_mode,
            "total_bookings": photographer.total_bookings,
            "completed_bookings": photographer.completed_bookings,
            "cancelled_bookings": photographer.cancelled_bookings,
        }
        for photographer in photographer_performance
    ]

    # 5. Prepare response
    data = {
        "total_photographers": total_photographers,
        "verified_photographers": verified_photographers,
        "unverified_photographers": unverified_photographers,
        "gold_photographers": gold_photographers,
        "platinum_photographers": platinum_photographers,
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "cancelled_bookings": cancelled_bookings,
        "photographer_performance": performance_data,
    }

    serializer = AdminPhotographerReportsSerializer(data)

    return Response(
        {
            "success": True,
            "message": "Photographer reports retrieved successfully.",
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,

    )


class PhotographerReportsPagination(PageNumberPagination):
    page_size = 5
    page_query_param = "page"


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Enter the page number (e.g. 1, 2, 3)",
            type=openapi.TYPE_INTEGER,
            required=False,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_photographer_reports(request):
    photographers = PhotographerProfile.objects.all()

    # Photographer performance and booking counts
    photographer_performance = (
        photographers
        .annotate(
            total_bookings=Count("bookings", distinct=True),
            completed_bookings=Count(
                "bookings",
                filter=Q(bookings__status="completed"),
                distinct=True,
            ),
            cancelled_bookings=Count(
                "bookings",
                filter=Q(bookings__status="cancelled"),
                distinct=True,
            ),
        )
        .order_by("-total_bookings", "id")
    )

    # Prepare photographer data
    performance_data = [
        {
            "photographer_id": photographer.id,
            "username": photographer.user.username,
            "is_verified": photographer.is_verified,
            "plan_mode": photographer.plan_mode,
            "total_bookings": photographer.total_bookings,
            "completed_bookings": photographer.completed_bookings,
            "cancelled_bookings": photographer.cancelled_bookings,
        }
        for photographer in photographer_performance
    ]

    # Apply pagination
    paginator = PhotographerReportsPagination()
    paginated_data = paginator.paginate_queryset(
        performance_data, request, view=None
    )

    # Serialize the current page
    serializer = PhotographerPerformanceSerializer(
        paginated_data, many=True
    )

    # Return requested response format
    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )



class UserReportsPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Enter page number (1, 2, 3, ...)",
            type=openapi.TYPE_INTEGER,
            required=False,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_user_reports(request):
    users = (
        User.objects
        .annotate(total_bookings=Count("bookings", distinct=True))
        .order_by("-date_joined", "-id")
    )

    # Overall user statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()

    today = timezone.localdate()
    first_day_of_month = today.replace(day=1)

    new_users_this_month = users.filter(
        date_joined__date__gte=first_day_of_month,
        date_joined__date__lte=today,
    ).count()

    # Pagination
    paginator = UserReportsPagination()
    paginated_users = paginator.paginate_queryset(
        users, request, view=None
    )

    user_data = [
        {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "date_joined": user.date_joined,
            "total_bookings": user.total_bookings,
        }
        for user in paginated_users
    ]

    serializer = UserReportItemSerializer(user_data, many=True)

    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "statistics": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "new_users_this_month": new_users_this_month,
            },
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

class ActivityLogPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "page"


@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "page",
            openapi.IN_QUERY,
            description="Enter page number (1, 2, 3, ...)",
            type=openapi.TYPE_INTEGER,
            required=False,
        )
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def admin_activity_logs(request):
    logs = ActivityLog.objects.all().order_by("-created_at", "-id")

    paginator = ActivityLogPagination()
    paginated_logs = paginator.paginate_queryset(
        logs, request, view=None
    )

    serializer = ActivityLogSerializer(paginated_logs, many=True)

    return Response(
        {
            "success": True,
            "count": paginator.page.paginator.count,
            "total_pages": paginator.page.paginator.num_pages,
            "current_page": paginator.page.number,
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "data": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

