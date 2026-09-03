from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils import swagger_auto_schema

from user.models import UserProfile,Booking
from photographer.models import PhotographerProfile
from .serializers import PendingPhotographerSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from drf_yasg import openapi
from .models import PlatformFee
from .serializers import (
    AdminLoginSerializer,
    UserListSerializer,
    PhotographerListSerializer,
    AdminBookingManagementSerializer,PlatformFeeSerializer
)


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
            "search",
            openapi.IN_QUERY,
            description="Search photographer by first name or last name",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    responses={200: PhotographerListSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def search_photographers(request):

    search = request.GET.get("search", "").strip()

    if not search:
        return Response([])

    photographers = PhotographerProfile.objects.filter(
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search)
    )

    serializer = PhotographerListSerializer(
        photographers,
        many=True
    )

    return Response(serializer.data)



@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "search",
            openapi.IN_QUERY,
            description="Search user by username or name",
            type=openapi.TYPE_STRING,
            required=True,
        ),
    ],
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def search_users(request):

    search = request.GET.get("search", "").strip()

    if not search:
        return Response(
            {
                "error": "Please enter a username or name."
            },
            status=400
        )

    users = UserProfile.objects.select_related(
        "user"
    ).filter(
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search)
    )

    serializer = UserListSerializer(
        users,
        many=True
    )

    return Response(serializer.data)


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