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
from user.models import Notification
from user.serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import WeeklyAvailability, AvailabilityException
from .serializers import WeeklyAvailabilitySerializer,AvailabilityExceptionSerializer
from datetime import date, timedelta

def check_photographer_verification(request):

    profile = request.user.photographer_profile

    if not profile.is_verified:
        return Response(
            {
                "error": "Your account is waiting for admin approval."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    return None

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
    data=request.data
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_notifications(request):
    response = check_photographer_verification(request)
    if response:
        return response

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by("-created_at")

    serializer = NotificationSerializer(
        notifications,
        many=True
    )

    return Response(serializer.data)

@swagger_auto_schema(
    method="post",
    request_body=WeeklyAvailabilitySerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_weekly_availability(request):

    profile = request.user.photographer_profile

    serializer = WeeklyAvailabilitySerializer(data=request.data)

    if serializer.is_valid():

        weekday = serializer.validated_data["weekday"]

        if WeeklyAvailability.objects.filter(
            photographer=profile,
            weekday=weekday
        ).exists():

            return Response(
                {
                    "error": "Availability already exists for this weekday."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(
            photographer=profile
        )

        return Response(
            {
                "message": "Weekly availability added successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# @swagger_auto_schema(
#     method="get",
#     responses={200: WeeklyAvailabilitySerializer(many=True)}
# )
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def my_weekly_availability(request):

#     profile = request.user.photographer_profile

#     availability = WeeklyAvailability.objects.filter(
#         photographer=profile
#     ).order_by("weekday")
    

#     serializer = WeeklyAvailabilitySerializer(
#         availability,
#         many=True
#     )

#     return Response(serializer.data)
@swagger_auto_schema(
    method="get",
    responses={200: WeeklyAvailabilitySerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_weekly_availability(request):

    profile = request.user.photographer_profile

    availability = WeeklyAvailability.objects.filter(
        photographer=profile
    ).order_by("weekday")

    today = date.today()

    data = []

    for item in availability:

        # Calculate next occurrence of this weekday
        days_ahead = (item.weekday - today.weekday()) % 7

        next_date = today + timedelta(days=days_ahead)

        data.append({
            "id": item.id,
            "weekday": item.weekday,
            "weekday_name": item.get_weekday_display(),
            "date": next_date,
            "morning": item.morning,
            "afternoon": item.afternoon,
        })

    return Response(data)




@swagger_auto_schema(
    method="patch",
    request_body=WeeklyAvailabilitySerializer
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_weekly_availability(request, availability_id):

    profile = request.user.photographer_profile

    try:

        availability = WeeklyAvailability.objects.get(
            id=availability_id,
            photographer=profile
        )

    except WeeklyAvailability.DoesNotExist:

        return Response(
            {
                "error": "Availability not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = WeeklyAvailabilitySerializer(
        availability,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():

        if "weekday" in serializer.validated_data:

            weekday = serializer.validated_data["weekday"]

            exists = WeeklyAvailability.objects.filter(
                photographer=profile,
                weekday=weekday
            ).exclude(
                id=availability.id
            ).exists()

            if exists:

                return Response(
                    {
                        "error": "Availability already exists for this weekday."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer.save()

        return Response(
            {
                "message": "Availability updated successfully.",
                "data": serializer.data
            }
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )



@swagger_auto_schema(method="delete")
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_weekly_availability(request, availability_id):

    profile = request.user.photographer_profile

    try:

        availability = WeeklyAvailability.objects.get(
            id=availability_id,
            photographer=profile
        )

    except WeeklyAvailability.DoesNotExist:

        return Response(
            {
                "error": "Availability not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    availability.delete()

    return Response(
        {
            "message": "Availability deleted successfully."
        }
    )


@swagger_auto_schema(
    method="post",
    request_body=AvailabilityExceptionSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_availability_exception(request):

    profile = request.user.photographer_profile

    serializer = AvailabilityExceptionSerializer(data=request.data)

    if serializer.is_valid():

        date = serializer.validated_data["date"]
        session = serializer.validated_data["session"]

        if AvailabilityException.objects.filter(
            photographer=profile,
            date=date,
            session=session
        ).exists():

            return Response(
                {
                    "error": "Exception already exists."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(
            photographer=profile
        )

        return Response(
            {
                "message": "Exception added successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )



@swagger_auto_schema(
    method="get",
    responses={200: AvailabilityExceptionSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_availability_exceptions(request):

    profile = request.user.photographer_profile

    exceptions = AvailabilityException.objects.filter(
        photographer=profile
    ).order_by("date")

    serializer = AvailabilityExceptionSerializer(
        exceptions,
        many=True
    )

    return Response(serializer.data)




@swagger_auto_schema(method="delete")
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_availability_exception(request, exception_id):

    profile = request.user.photographer_profile

    try:

        exception = AvailabilityException.objects.get(
            id=exception_id,
            photographer=profile
        )

    except AvailabilityException.DoesNotExist:

        return Response(
            {
                "error": "Exception not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    exception.delete()

    return Response(
        {
            "message": "Exception deleted successfully."
        }
    )