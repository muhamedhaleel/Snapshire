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
from .serializers import VerificationSerializer,AvailabilitySerializer,MyAvailabilitySerializer
import calendar
from datetime import datetime, date
from .models import Availability




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

@swagger_auto_schema(
    method="post",
    request_body=AvailabilitySerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def save_availability(request):

    serializer = AvailabilitySerializer(data=request.data)

    if serializer.is_valid():

        profile = request.user.photographer_profile

        availability, created = Availability.objects.update_or_create(

            photographer=profile,

            date=serializer.validated_data["date"],

            defaults={

                "morning_status": serializer.validated_data["morning_status"],

                "afternoon_status": serializer.validated_data["afternoon_status"],

            }

        )

        return Response({

            "message":"Availability saved successfully.",

            "data":AvailabilitySerializer(availability).data

        })

    return Response(serializer.errors,status=400)


import calendar
from datetime import datetime, date

@swagger_auto_schema(method="get")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def calendar_view(request):

    profile = request.user.photographer_profile

    today = datetime.today()

    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    total_days = calendar.monthrange(year, month)[1]

    saved = Availability.objects.filter(

        photographer=profile,

        date__year=year,

        date__month=month

    )

    saved_dates = {

        item.date:item

        for item in saved

    }

    data=[]

    for day in range(1,total_days+1):

        current_date=date(year,month,day)

        if current_date in saved_dates:

            item=saved_dates[current_date]

            data.append({

                "id":item.id,

                "date":current_date,

                "morning_status":item.morning_status,

                "afternoon_status":item.afternoon_status

            })

        else:

            data.append({

                "id":None,

                "date":current_date,

                "morning_status":"unavailable",

                "afternoon_status":"unavailable"

            })

    return Response(data)

@swagger_auto_schema(
    method="put",
    request_body=AvailabilitySerializer
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def update_availability(request, id):

    profile = request.user.photographer_profile

    try:
        availability = Availability.objects.get(
            id=id,
            photographer=profile
        )

    except Availability.DoesNotExist:
        return Response(
            {
                "error": "Availability not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = AvailabilitySerializer(
        availability,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        serializer.save()

        return Response(
            {
                "message": "Availability updated successfully.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method="delete")
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_availability(request, id):

    profile = request.user.photographer_profile

    try:
        availability = Availability.objects.get(
            id=id,
            photographer=profile
        )

    except Availability.DoesNotExist:
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
        },
        status=status.HTTP_200_OK
    )


@swagger_auto_schema(
    method="get",
    responses={200: MyAvailabilitySerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_availability(request):

    profile = request.user.photographer_profile

    availability = Availability.objects.filter(
        photographer=profile
    ).order_by("date")

    serializer = MyAvailabilitySerializer(
        availability,
        many=True
    )

    return Response(serializer.data)