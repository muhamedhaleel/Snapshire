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
from photographer.models import Availability
from .serializers import PhotographerViewSerializer,PhotographerDetailSerializer,PhotographerAvailabilitySerializer
from datetime import datetime
import calendar
from .models import Booking
from .serializers import BookingSerializer,UserBookingStatusSerializer
from decimal import Decimal
from .models import Notification
from .serializers import NotificationSerializer



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




@swagger_auto_schema(
    method="get",
    responses={200: PhotographerDetailSerializer}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_detail(request, id):

    try:
        photographer = PhotographerProfile.objects.select_related("user").get(
            id=id,
            user__is_active=True,
            is_verified=True
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {
                "error": "Photographer not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PhotographerDetailSerializer(photographer)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_availability(request, photographer_id):

    try:
        photographer = PhotographerProfile.objects.get(
            id=photographer_id,
            is_verified=True,
            user__is_active=True
        )

    except PhotographerProfile.DoesNotExist:
        return Response(
            {"error": "Photographer not found."},
            status=404
        )

    today = datetime.today()

    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    availability = Availability.objects.filter(
        photographer=photographer,
        date__year=year,
        date__month=month
    ).order_by("date")

    data = []

    ACTIVE_BOOKING_STATUS = [
        "payment_pending",
        "waiting_photographer",
        "photographer_accepted",
        "waiting_admin",
        "confirmed",
        "completed",
    ]

    for item in availability:

        morning = item.morning_status
        afternoon = item.afternoon_status

        morning_booked = Booking.objects.filter(
            photographer=photographer,
            date=item.date,
            session="morning",
            status__in=ACTIVE_BOOKING_STATUS
        ).exists()

        afternoon_booked = Booking.objects.filter(
            photographer=photographer,
            date=item.date,
            session="afternoon",
            status__in=ACTIVE_BOOKING_STATUS
        ).exists()

        if morning_booked:
            morning = "unavailable"

        if afternoon_booked:
            afternoon = "unavailable"

        data.append({
            "id": item.id,
            "date": item.date,
            "morning_status": morning,
            "afternoon_status": afternoon
        })

    return Response(data)

@swagger_auto_schema(
    method="post",
    request_body=BookingSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):

    serializer = BookingSerializer(data=request.data)

    if serializer.is_valid():

        photographer = serializer.validated_data["photographer"]
        booking_date = serializer.validated_data["date"]
        session = serializer.validated_data["session"]

        # Check photographer verification
        if not photographer.is_verified:

            return Response(
                {
                    "error": "Photographer is not verified."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check availability exists
        try:

            availability = Availability.objects.get(
                photographer=photographer,
                date=booking_date
            )

        except Availability.DoesNotExist:

            return Response(
                {
                    "error": "Photographer is not available on this date."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check session availability
        if session == "morning":

            if availability.morning_status != "available":

                return Response(
                    {
                        "error": "Morning session is unavailable."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif session == "afternoon":

            if availability.afternoon_status != "available":

                return Response(
                    {
                        "error": "Afternoon session is unavailable."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Prevent double booking
        booking_exists = Booking.objects.filter(
            photographer=photographer,
            date=booking_date,
            session=session,
            status__in=[
                "payment_pending",
                "waiting_photographer",
                "photographer_accepted",
                "waiting_admin",
                "confirmed"
            ]
        ).exists()

        if booking_exists:

            return Response(
                {
                    "error": "This session has already been booked."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    active_booking = Booking.objects.filter(
    user=request.user,
    status__in=[
        "payment_pending",
        "waiting_photographer",
        "photographer_accepted",
        "waiting_admin",
        "confirmed",
    ]
    ).exists()

    if active_booking:
        return Response(
            {
                "error": "You already have an active booking. Complete or cancel it before booking another photographer."
            },
            status=status.HTTP_400_BAD_REQUEST
        )





        # ------------------------
        # Price Calculation
        # ------------------------

        try:
            experience = int(photographer.experience)

        except:

            experience = 1

        hourly_rate = experience * 200

        hours = serializer.validated_data["hours"]

        platform_fee = Decimal("15.00")

        total_amount = Decimal(hourly_rate * hours) + platform_fee

        advance_amount = total_amount * Decimal("0.50")

        balance_amount = total_amount - advance_amount

        # ------------------------
        # Create Booking
        # ------------------------

        booking = Booking.objects.create(

            user=request.user,

            photographer=photographer,

            date=booking_date,

            session=session,

            location=serializer.validated_data["location"],

            shoot_time=serializer.validated_data["shoot_time"],

            hours=hours,

            requirements=serializer.validated_data["requirements"],

            total_amount=total_amount,

            advance_amount=advance_amount,

            balance_amount=balance_amount,

            status="payment_pending"

        )

        return Response(

            {

                "message": "Booking created successfully.",

                "booking_id": booking.id,

                "total_amount": booking.total_amount,

                "advance_amount": booking.advance_amount,

                "balance_amount": booking.balance_amount,

                "status": booking.status

            },

            status=status.HTTP_201_CREATED

        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )



@swagger_auto_schema(
    method="get",
    responses={200: UserBookingStatusSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_booking_status(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).select_related(
        "photographer",
        "photographer__user"
    ).order_by("-created_at")

    serializer = UserBookingStatusSerializer(
        bookings,
        many=True
    )

    return Response(serializer.data)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_notifications(request):

    notifications = Notification.objects.filter(
        user=request.user
    )

    serializer = NotificationSerializer(
        notifications,
        many=True
    )
    return Response(serializer.data)