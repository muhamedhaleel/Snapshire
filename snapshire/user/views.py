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
from .serializers import PhotographerViewSerializer,PhotographerDetailSerializer,PhotographerFilterSerializer
from .models import Booking
from .serializers import BookingSerializer,UserBookingStatusSerializer
from decimal import Decimal
from .models import Notification
from .serializers import NotificationSerializer
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from photographer.models import PhotographerProfile,WeeklyAvailability,AvailabilityException
from datetime import date, timedelta
from datetime import datetime




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
    method="patch",
    request_body=UpdateProfileSerializer
)
@api_view(["PATCH"])
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
    ).order_by("-created_at")

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

    days = int(request.GET.get("days", 30))

    today = date.today()

    end_date = today + timedelta(days=days)

    data = []

    ACTIVE_STATUS = [
        "payment_pending",
        "waiting_photographer",
        "photographer_accepted",
        "waiting_admin",
        "confirmed",
        "completed",
    ]

    current = today

    while current <= end_date:

        weekday = current.isoweekday()

        weekly = WeeklyAvailability.objects.filter(
            photographer=photographer,
            weekday=weekday
        ).first()

        if weekly:

            morning = weekly.morning
            afternoon = weekly.afternoon

            exceptions = AvailabilityException.objects.filter(
                photographer=photographer,
                date=current
            )

            for exception in exceptions:

                if exception.session == "full_day":
                    morning = False
                    afternoon = False

                elif exception.session == "morning":
                    morning = False

                elif exception.session == "afternoon":
                    afternoon = False

            if Booking.objects.filter(
                photographer=photographer,
                date=current,
                session="morning",
                status__in=ACTIVE_STATUS
            ).exists():
                morning = False

            if Booking.objects.filter(
                photographer=photographer,
                date=current,
                session="afternoon",
                status__in=ACTIVE_STATUS
            ).exists():
                afternoon = False

            if morning or afternoon:

                data.append({

                    "date": current,

                    "morning": morning,

                    "afternoon": afternoon

                })

        current += timedelta(days=1)

    return Response(data)

# @swagger_auto_schema(
#     method="post",
#     request_body=BookingSerializer
# )
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def create_booking(request):

#     serializer = BookingSerializer(data=request.data)

#     if serializer.is_valid():

#         photographer = serializer.validated_data["photographer"]
#         booking_date = serializer.validated_data["date"]
#         session = serializer.validated_data["session"]

#         # Check photographer verification
#         if not photographer.is_verified:

#             return Response(
#                 {
#                     "error": "Photographer is not verified."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Check availability exists
#         try:

#             availability = Availability.objects.get(
#                 photographer=photographer,
#                 date=booking_date
#             )

#         except Availability.DoesNotExist:

#             return Response(
#                 {
#                     "error": "Photographer is not available on this date."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # Check session availability
#         if session == "morning":

#             if availability.morning_status != "available":

#                 return Response(
#                     {
#                         "error": "Morning session is unavailable."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         elif session == "afternoon":

#             if availability.afternoon_status != "available":

#                 return Response(
#                     {
#                         "error": "Afternoon session is unavailable."
#                     },
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # Prevent double booking
#         booking_exists = Booking.objects.filter(
#             photographer=photographer,
#             date=booking_date,
#             session=session,
#             status__in=[
#                 "payment_pending",
#                 "waiting_photographer",
#                 "photographer_accepted",
#                 "waiting_admin",
#                 "confirmed"
#             ]
#         ).exists()

#         if booking_exists:

#             return Response(
#                 {
#                     "error": "This session has already been booked."
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#     active_booking = Booking.objects.filter(
#     user=request.user,
#     status__in=[
#         "payment_pending",
#         "waiting_photographer",
#         "photographer_accepted",
#         "waiting_admin",
#         "confirmed",
#     ]
#     ).exists()

#     if active_booking:
#         return Response(
#             {
#                 "error": "You already have an active booking. Complete or cancel it before booking another photographer."
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )





#     # ------------------------
#     # Price Calculation
#     # ------------------------

#     try:
#         experience = int(photographer.experience)

#     except:

#         experience = 1

#         hourly_rate = experience * 200

#         hours = serializer.validated_data["hours"]

#         platform_fee = Decimal("15.00")

#         total_amount = Decimal(hourly_rate * hours) + platform_fee

#         advance_amount = total_amount * Decimal("0.50")

#         balance_amount = total_amount - advance_amount

#         # ------------------------
#         # Create Booking
#         # ------------------------

#         booking = Booking.objects.create(

#             user=request.user,

#             photographer=photographer,

#             date=booking_date,

#             session=session,

#             location=serializer.validated_data["location"],

#             shoot_time=serializer.validated_data["shoot_time"],

#             hours=hours,

#             requirements=serializer.validated_data["requirements"],

#             total_amount=total_amount,

#             advance_amount=advance_amount,

#             balance_amount=balance_amount,

#             status="payment_pending"

#         )

#         return Response(

#             {

#                 "message": "Booking created successfully.",

#                 "booking_id": booking.id,

#                 "total_amount": booking.total_amount,

#                 "advance_amount": booking.advance_amount,

#                 "balance_amount": booking.balance_amount,

#                 "status": booking.status

#             },

#             status=status.HTTP_201_CREATED

#         )

#     return Response(
#         serializer.errors,
#         status=status.HTTP_400_BAD_REQUEST
#     )


@swagger_auto_schema(
    method="post",
    request_body=BookingSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_booking(request):

    serializer = BookingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    photographer = serializer.validated_data["photographer"]
    booking_date = serializer.validated_data["date"]
    session = serializer.validated_data["session"]

    # ------------------------
    # Check photographer verification
    # ------------------------

    if not photographer.is_verified:
        return Response(
            {"error": "Photographer is not verified."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ------------------------
    # Check Weekly Availability
    # ------------------------

    weekday = booking_date.isoweekday()

    weekly = WeeklyAvailability.objects.filter(
        photographer=photographer,
        weekday=weekday
    ).first()

    if not weekly:
        return Response(
            {"error": "Photographer is not available on this day."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if session == "morning" and not weekly.morning:
        return Response(
            {"error": "Morning session is unavailable."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if session == "afternoon" and not weekly.afternoon:
        return Response(
            {"error": "Afternoon session is unavailable."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ------------------------
    # Check Blacklist (Exceptions)
    # ------------------------

    blocked = AvailabilityException.objects.filter(
        photographer=photographer,
        date=booking_date
    ).filter(
        Q(session=session) |
        Q(session="full_day")
    ).exists()

    if blocked:
        return Response(
            {"error": "Photographer is unavailable on this date."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ------------------------
    # Prevent Double Booking
    # ------------------------

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
            {"error": "This session has already been booked."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ------------------------
    # Prevent Multiple Active Bookings
    # ------------------------

    active_booking = Booking.objects.filter(
        user=request.user,
        status__in=[
            "payment_pending",
            "waiting_photographer",
            "photographer_accepted",
            "waiting_admin",
            "confirmed"
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
    except ValueError:
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
            "photographer": photographer.user.username,
            "date": booking.date,
            "session": booking.session,
            "location": booking.location,
            "total_amount": booking.total_amount,
            "advance_amount": booking.advance_amount,
            "balance_amount": booking.balance_amount,
            "status": booking.status
        },
        status=status.HTTP_201_CREATED
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


@swagger_auto_schema(
    method="get",
    
    operation_description="Filter photographers by location, available date, or experience.",

    manual_parameters=[

        openapi.Parameter(
            name="location",
            in_=openapi.IN_QUERY,
            description="Photographer location (Example: Kochi)",
            type=openapi.TYPE_STRING,
            required=False,
        ),

        openapi.Parameter(
            name="date",
            in_=openapi.IN_QUERY,
            description="Booking date (YYYY-MM-DD)",
            type=openapi.TYPE_STRING,
            format="date",
            required=False,
        ),

        openapi.Parameter(
            name="experience",
            in_=openapi.IN_QUERY,
            description="Sort by experience",
            type=openapi.TYPE_STRING,
            enum=["asc", "desc"],
            required=False,
        ),
    ],
)

@api_view(["GET"])
def photographer_filter(request):

    location = request.GET.get("location")
    booking_date = request.GET.get("date")
    experience = request.GET.get("experience")

    # Require at least one filter
    if not (location or booking_date or experience):
        return Response(
            {
                "error": "Please provide at least one filter."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    photographers = PhotographerProfile.objects.filter(
        is_verified=True,
        user__is_active=True
    )

    # ------------------------
    # Filter by Location
    # ------------------------

    if location:
        photographers = photographers.filter(
            location__icontains=location
        )

    # ------------------------
    # Filter by Date
    # ------------------------

    if booking_date:

        try:
            booking_date = datetime.strptime(
                booking_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            return Response(
                {
                    "error": "Invalid date format. Use YYYY-MM-DD."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        weekday = booking_date.isoweekday()

        photographers = photographers.filter(
            weekly_availability__weekday=weekday
        ).exclude(
            availability_exceptions__date=booking_date,
            availability_exceptions__session="full_day"
        ).distinct()

    # ------------------------
    # Sort by Experience
    # ------------------------

    if experience:

        if experience.lower() == "asc":

            photographers = photographers.order_by("experience")

        elif experience.lower() == "desc":

            photographers = photographers.order_by("-experience")

        else:

            return Response(
                {
                    "error": "Experience must be 'asc' or 'desc'."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    serializer = PhotographerFilterSerializer(
        photographers,
        many=True
    )

    return Response(serializer.data)