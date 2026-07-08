from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.decorators import api_view,parser_classes,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer,UpdateProfileSerializer
from .models import UserProfile
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from photographer.models import PhotographerProfile
from .serializers import PhotographerViewSerializer


@swagger_auto_schema(
    method="post",
    request_body=SignupSerializer,
    responses={201: "Signup Successful"}
)
@api_view(["POST"])
@parser_classes([FormParser])
def signup(request):
    

    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

        return Response(
            {"message": "Signup Successful"},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    request_body=LoginSerializer,
    responses={200: "Login Successful"}
)
@api_view(["POST"])
@parser_classes([FormParser])
def login(request):

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Login Successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.username,
            "email": user.email,
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="put",
    request_body=UpdateProfileSerializer
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def profile_update(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    serializer = UpdateProfileSerializer(
        profile,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)




@swagger_auto_schema(
    method="get",
    responses={200: UpdateProfileSerializer}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    serializer = UpdateProfileSerializer(profile)

    return Response(serializer.data)


@swagger_auto_schema(
    method="get",
    responses={200: PhotographerViewSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_photographers(request):

    photographers = PhotographerProfile.objects.filter(
        user__is_active=True,
        is_verified=True
    )

    serializer = PhotographerViewSerializer(
        photographers,
        many=True
    )

    return Response(serializer.data)