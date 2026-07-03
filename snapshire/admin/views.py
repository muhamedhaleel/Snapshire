from rest_framework.decorators import api_view, parser_classes,permission_classes
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAdminUser
from .serializers import UserListSerializer
from .serializers import AdminLoginSerializer,PhotographerListSerializer
from rest_framework import status
from django.contrib.auth.models import User


@swagger_auto_schema(
    method="post",
    request_body=AdminLoginSerializer,
    responses={200: "Admin Login Successful"}
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
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )

@swagger_auto_schema(
    method="get",
    responses={200: UserListSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def user_list(request):

    users = User.objects.filter(is_superuser=False)

    serializer = UserListSerializer(
        users,
        many=True
    )

    return Response(serializer.data)


@swagger_auto_schema(
    method="patch",
    responses={200: "User Blocked Successfully"}
)
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def block_user(request, user_id):

    try:
        user = User.objects.get(
            id=user_id,
            is_superuser=False
        )

    except User.DoesNotExist:

        return Response(
            {
                "error": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    user.is_active = False
    user.save()

    return Response(
        {
            "message": "User blocked successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "status": "Blocked"
            }
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="patch",
    responses={200: "User Unblocked Successfully"}
)
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def unblock_user(request, user_id):

    try:
        user = User.objects.get(
            id=user_id,
            is_superuser=False
        )

    except User.DoesNotExist:

        return Response(
            {
                "error": "User not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    user.is_active = True
    user.save()

    return Response(
        {
            "message": "User unblocked successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "status": "Active"
            }
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="get",
    responses={200: PhotographerListSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def photographer_list(request):

    photographers = User.objects.filter(
        photographer_profile__isnull=False,
        is_superuser=False
    )

    serializer = PhotographerListSerializer(
        photographers,
        many=True
    )

    return Response(serializer.data)

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def block_photographer(request, photographer_id):

    try:
        user = User.objects.get(
            id=photographer_id,
            photographer_profile__isnull=False
        )

    except User.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    user.is_active = False
    user.save()

    return Response({
        "message": "Photographer blocked successfully."
    })


@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def unblock_photographer(request, photographer_id):

    try:
        user = User.objects.get(
            id=photographer_id,
            photographer_profile__isnull=False
        )

    except User.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    user.is_active = True
    user.save()

    return Response({
        "message": "Photographer unblocked successfully."
    })

@swagger_auto_schema(method="patch")
@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def verify_photographer(request, photographer_id):

    try:
        profile = User.objects.get(
            id=photographer_id,
            photographer_profile__isnull=False
        ).photographer_profile

    except User.DoesNotExist:

        return Response(
            {"error": "Photographer not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    profile.is_verified = True
    profile.verification_status = "Approved"
    profile.save()

    return Response({
        "message": "Photographer verified successfully.",
        "verification_status": profile.verification_status,
        "is_verified": profile.is_verified
    })