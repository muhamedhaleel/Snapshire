import os
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import SignupSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer,UpdatePhotographerProfileSerializer,PhotographerProfileSerializer
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from .serializers import VerificationSerializer


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
            {
                "message": "Photographer registered successfully."
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )
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

        # Check whether this user has a photographer profile
        try:
            user.photographer_profile
        except:
            return Response(
                {
                    "error": "Photographer account not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login Successful",

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
    method="put",
    request_body=UpdatePhotographerProfileSerializer,
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def profile_update(request):

    serializer = UpdatePhotographerProfileSerializer(

        request.user.photographer_profile,

        data=request.data,

        partial=True

    )

    if serializer.is_valid():

        serializer.save()

        return Response(serializer.data)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="get",
    responses={200: PhotographerProfileSerializer}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile(request):

    serializer = PhotographerProfileSerializer(
        request.user.photographer_profile
    )

    return Response(serializer.data)




@swagger_auto_schema(
    method="post",
    request_body=VerificationSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def verification(request):

    serializer = VerificationSerializer(data=request.data)

    if serializer.is_valid():

        profile = request.user.photographer_profile
        plan = serializer.validated_data["plan_mode"]

        # Prevent selecting the same plan again
        if profile.plan_mode == plan:
            return Response(
                {
                    "message": f"You are already using the {plan.capitalize()} plan."
                },
                status=status.HTTP_200_OK
            )

        if plan == "free":

            profile.plan_mode = "free"
            profile.save()

            return Response(
                {
                    "message": "Free plan activated successfully.",
                    "plan_mode": profile.plan_mode
                },
                status=status.HTTP_200_OK
            )

        if plan == "gold":

            return Response(
                {
                    "message": "Gold plan requires payment. Payment integration will be available soon."
                },
                status=status.HTTP_200_OK
            )

        if plan == "platinum":

            return Response(
                {
                    "message": "Platinum plan requires payment. Payment integration will be available soon."
                },
                status=status.HTTP_200_OK
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)