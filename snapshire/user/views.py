from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.decorators import api_view,parser_classes,permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer,UpdateProfileSerializer,CreateBalancePaymentSerializer,UserWalletSerializer,WalletTransactionSerializer,CancelBookingRequestSerializer
from .models import UserProfile
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import FormParser
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from photographer.models import PhotographerProfile
from .serializers import PhotographerViewSerializer,PhotographerDetailSerializer,PhotographerFilterSerializer,CreatePaymentSerializer,VerifyPaymentSerializer,CancelBookingSerializer,RescheduleRequestSerializer
from .models import Booking,UserWallet,WalletTransaction
from .serializers import BookingSerializer,UserBookingStatusSerializer,VerifyOTPSerializer,UserFeedbackListSerializer
from decimal import Decimal
from .models import Notification,RescheduleRequest
from .serializers import NotificationSerializer,ForgotPasswordSerializer,ResetPasswordSerializer,BookingPaymentDetailsSerializer,CreateFeedbackSerializer,GoogleLoginSerializer
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg import openapi
from photographer.models import PhotographerProfile,WeeklyAvailability,AvailabilityException,PhotographerCharge
from datetime import date, timedelta
from datetime import datetime
import random
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailOTP
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from .models import EmailOTP, UserProfile, PasswordResetOTP
from decimal import Decimal
from admin.models import PlatformFee

import razorpay
from rest_framework_simplejwt.tokens import RefreshToken

from django.conf import settings

from .models import Booking, Payment,Feedback
from google.oauth2 import id_token
from google.auth.transport import requests
from .models import UserProfile

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes
)

from rest_framework.parsers import (
    FormParser,
    MultiPartParser
)




# @swagger_auto_schema(
#     method="post",
#     request_body=SignupSerializer,
#     responses={201: "Signup Successful"}
# )
# @api_view(["POST"])
# @parser_classes([FormParser])
# def signup(request):
    

#     serializer = SignupSerializer(data=request.data)

#     if serializer.is_valid():
#         serializer.save()

#         return Response(
#             {"message": "Signup Successful"},
#             status=status.HTTP_201_CREATED
#         )

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    request_body=SignupSerializer,
    responses={200: "OTP Sent Successfully"}
)
@api_view(["POST"])
@parser_classes([FormParser])
def signup(request):

    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():

        username = serializer.validated_data["username"].strip()
        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Remove previous OTP if exists
        EmailOTP.objects.filter(email=email).delete()

        # Save new OTP
        EmailOTP.objects.create(
            email=email,
            username=username,
            password=password,
            otp=otp,
            created_at=timezone.now()
        )

        # Send OTP Email
        send_mail(
            subject="Snapshire Email Verification",
            message=f"""
            
            Hellow,
            Here is your OTP for Snapshire signup:{otp}
            This OTP is valid for 5 minutes.
            Continue with Snapshire for the best photography experience!
            """,
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "OTP sent successfully. Please verify your email."
            },
            status=status.HTTP_200_OK
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
        # Create notification
        Notification.objects.create(
            user=request.user,
            title="Profile Updated",
            message="Your profile has been updated successfully."
        )

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
        is_verified=True,
        charges__isnull=False
    ).select_related(
        "user"
    ).prefetch_related(
        "charges"
    ).distinct().order_by("-created_at")
    

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
        photographer = PhotographerProfile.objects.select_related("user").prefetch_related("charges").get(
            id=id,
            user__is_active=True,
            is_verified=True,
            charges__isnull=False
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

        weekday = current.weekday()

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
@parser_classes([FormParser])
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

    weekday = booking_date.weekday()

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

    

    # ------------------------
    # Price Calculation
    # ------------------------

    # hours = serializer.validated_data["hours"]

    
    # charge = PhotographerCharge.objects.filter(
    #     photographer=photographer
    # ).order_by("hours").first()

    # if not charge:
    #     return Response(
    #     {
    #         "success": False,
    #         "message": (
    #             "Service charge has not been configured "
    #             "for this photographer."
    #         )
    #     },
    #     status=status.HTTP_400_BAD_REQUEST
    # )

    


    # hourly_rate = Decimal(str(charge.amount))

    # # Photographer's charge for selected hours
    # photographer_amount = hourly_rate * Decimal(str(hours))

    # # Fixed platform fee
    # fee = PlatformFee.objects.first()

    # if not fee:
    #     return Response(
    #         {
    #             "success": False,
    #             "message": "Platform fee has not been configured by admin."
    #         },
    #         status=status.HTTP_400_BAD_REQUEST
    #     )

    # platform_fee = fee.amount

    #  # Total booking amount
    # total_amount = (
    #     photographer_amount + platform_fee
    # )

    # # 50% advance payment
    # advance_amount = (
    #     total_amount / Decimal("2")
    # )

    # # Remaining 50%
    # balance_amount = (
    #     total_amount - advance_amount
    # )
    

    hours = serializer.validated_data["hours"]

    # -----------------------------------------
    # GET PHOTOGRAPHER HOURLY CHARGE
    # -----------------------------------------

    charge = PhotographerCharge.objects.filter(
        photographer=photographer
    ).order_by("hours").first()

    if not charge:
        return Response(
            {
                "success": False,
                "message": (
                    "Service charge has not been configured "
                    "for this photographer."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    hourly_rate = Decimal(str(charge.amount))

    # Photographer charge based on selected hours
    photographer_amount = (
        hourly_rate * Decimal(str(hours))
    )

    # -----------------------------------------
    # GET PLATFORM FEE
    # -----------------------------------------

    fee = PlatformFee.objects.first()

    if not fee:
        return Response(
            {
                "success": False,
                "message": (
                    "Platform fee has not been configured "
                    "by admin."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    platform_fee = Decimal(str(fee.amount))

    # -----------------------------------------
    # TOTAL BOOKING AMOUNT
    # -----------------------------------------

    total_amount = (
        photographer_amount + platform_fee
    )

    # -----------------------------------------
    # PAYMENT CALCULATION
    # -----------------------------------------

    # 50% of photographer amount
    photographer_advance = (
        photographer_amount / Decimal("2")
    )

    # Remaining 50% of photographer amount
    photographer_balance = (
        photographer_amount - photographer_advance
    )

    # Full platform fee is collected initially
    advance_amount = (
        photographer_advance + platform_fee
    )

    # Only remaining photographer amount is paid later
    balance_amount = photographer_balance

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
        hours=serializer.validated_data["hours"],
        requirements=serializer.validated_data["requirements"],
        photographer_amount=photographer_amount,
        platform_fee=platform_fee,
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
        "hours": booking.hours,
        "location": booking.location,

        "pricing": {
            "photographer_amount": booking.photographer_amount,
            "platform_fee": booking.platform_fee,
            "total_amount": (
                booking.photographer_amount +
                booking.platform_fee
            ),
            "advance_amount": booking.advance_amount,
            "balance_amount": booking.balance_amount,
        },

        "payment": {
            "pay_now": booking.advance_amount,
            "pay_after_photoshoot": booking.balance_amount,
        },

        "status": booking.status,
    },
    status=status.HTTP_201_CREATED
)
        

# @swagger_auto_schema(
#     method="get",
#     responses={200: UserBookingStatusSerializer(many=True)}
# )
# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def user_booking_status(request):

#     bookings = Booking.objects.filter(
#         user=request.user
#     ).select_related(
#         "photographer",
#         "photographer__user"
#     ).order_by("-created_at")

#     serializer = UserBookingStatusSerializer(
#         bookings,
#         many=True
#     )

#     return Response(serializer.data)

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
    ).prefetch_related(
        "payments"
    ).order_by("-created_at")

    serializer = UserBookingStatusSerializer(
        bookings,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": bookings.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )


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

        weekday = booking_date.weekday()

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



@swagger_auto_schema(
    method="post",
    request_body=VerifyOTPSerializer
)
@api_view(["POST"])
def verify_otp(request):

    serializer = VerifyOTPSerializer(data=request.data)

    if serializer.is_valid():

        email = serializer.validated_data["email"].lower()
        otp = serializer.validated_data["otp"]

        try:

            otp_record = EmailOTP.objects.get(email=email)

        except EmailOTP.DoesNotExist:

            return Response(
                {
                    "error": "OTP not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # OTP expires after 5 minutes
        if timezone.now() > otp_record.created_at + timedelta(minutes=5):

            otp_record.delete()

            return Response(
                {
                    "error": "OTP has expired."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp_record.otp != otp:

            return Response(
                {
                    "error": "Invalid OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create User
        user = User.objects.create(

            username=otp_record.username,
            email=otp_record.email,
            password=make_password(otp_record.password)

        )

        UserProfile.objects.create(user=user)

        otp_record.delete()

        return Response(
            {
                "message": "Signup Successful"
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def cancel_booking(request, booking_id):

#     try:
#         booking = Booking.objects.get(
#             id=booking_id,
#             user=request.user
#         )

#     except Booking.DoesNotExist:
#         return Response(
#             {
#                 "success": False,
#                 "message": "Booking not found."
#             },
#             status=status.HTTP_404_NOT_FOUND
#         )

#     # Cancellation allowed only before payment
#     if booking.status != "payment_pending":
#         return Response(
#             {
#                 "success": False,
#                 "message": "Booking cannot be cancelled at this stage."
#             },
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     booking.status = "cancelled"
#     booking.save(update_fields=["status"])

#     return Response(
#         {
#             "success": True,
#             "message": "Booking cancelled successfully."
#         },
#         status=status.HTTP_200_OK
#     )

from decimal import Decimal
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from rest_framework.decorators import (
    api_view,
    permission_classes
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema



@swagger_auto_schema(
    method="post",
    request_body=CancelBookingRequestSerializer,
    responses={
        200: CancelBookingSerializer
    }
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def cancel_booking(request, booking_id):


    #---------------------------------------------
    # 1. Validate cancellation reason
    # ---------------------------------------------

    serializer = CancelBookingRequestSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    cancellation_reason = serializer.validated_data[
        "cancellation_reason"
    ]

    # ==================================================
    # 1. GET BOOKING
    # ==================================================

    try:

        booking = Booking.objects.select_related(
            "photographer",
            "photographer__user"
        ).get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # ==================================================
    # 2. SAVE ORIGINAL STATUS
    # ==================================================

    original_status = booking.status

    # ==================================================
    # 3. ALREADY CANCELLED
    # ==================================================

    if booking.status == "cancelled":

        return Response(
            {
                "success": False,
                "message": "Booking is already cancelled."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==================================================
    # 4. COMPLETED BOOKING
    # ==================================================

    if booking.status == "completed":

        return Response(
            {
                "success": False,
                "message": "Completed bookings cannot be cancelled."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==================================================
    # 5. PAYMENT NOT COMPLETED
    # ==================================================

    if booking.status == "payment_pending":

        booking.status = "cancelled"
        booking.cancellation_reason = cancellation_reason


        booking.save(
            update_fields=[
                "status",
                "cancellation_reason"
            ]
        )

        return Response(
            {
                "success": True,
                "message": "Booking cancelled successfully.",
                "data": {
                    "booking_id": booking.id,
                    "booking_status": booking.status,
                    "photographer_status": original_status,
                    "advance_paid": "0.00",
                    "platform_fee": "0.00",
                    "refund_amount": "0.00",
                    "refund_status": "not_applicable"
                }
            },
            status=status.HTTP_200_OK
        )

    # ==================================================
    # 6. FIND PAID ADVANCE PAYMENT
    # ==================================================

    advance_payment = Payment.objects.filter(
        booking=booking,
        payment_type="advance",
        status="paid"
    ).first()

    if not advance_payment:

        return Response(
            {
                "success": False,
                "message": "Paid advance payment was not found."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==================================================
    # 7. CHECK CREATED TIME
    # ==================================================

    if not booking.created_at:

        return Response(
            {
                "success": False,
                "message": "Booking creation time is not available."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # ==================================================
    # 8. CALCULATE 24-HOUR REFUND WINDOW
    # ==================================================

    now = timezone.now()

    refund_deadline = (
        booking.created_at +
        timedelta(hours=24)
    )

    refund_allowed = (
        now <= refund_deadline
    )

    # ==================================================
    # 9. HOURS REMAINING
    # ==================================================

    remaining_seconds = (
        refund_deadline - now
    ).total_seconds()

    hours_remaining = max(
        remaining_seconds / 3600,
        0
    )

    # ==================================================
    # 10. PAYMENT AMOUNTS
    # ==================================================

    advance_paid = Decimal(
        str(advance_payment.amount)
    )

    platform_fee = Decimal(
        str(booking.platform_fee)
    )

    # ==================================================
    # 11. CALCULATE REFUND
    # ==================================================

    if refund_allowed:

        # Platform fee is NOT refundable

        refund_amount = (
            advance_paid - platform_fee
        )

        if refund_amount < Decimal("0.00"):

            refund_amount = Decimal("0.00")

        refund_status = "refunded"

    else:

        refund_amount = Decimal("0.00")

        refund_status = "not_refundable"

    # ==================================================
    # 12. DATABASE TRANSACTION
    # ==================================================

    with transaction.atomic():

    # Lock the payment row
        advance_payment = Payment.objects.select_for_update().get(
            id=advance_payment.id
    )

    # Cancel booking and save cancellation reason
        booking.status = "cancelled"
        booking.cancellation_reason = cancellation_reason

        booking.save(
            update_fields=[
                "status",
                "cancellation_reason"
            ]
    )

    

        # ----------------------------------------------
        # Prevent duplicate refund
        # ----------------------------------------------

        already_refunded = WalletTransaction.objects.filter(
            payment=advance_payment,
            transaction_type="refund",
            status="completed"
        ).exists()

        if already_refunded:

            return Response(
                {
                    "success": False,
                    "message": "Refund has already been processed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------
        # Cancel booking
        # ----------------------------------------------

        booking.status = "cancelled"
        booking.cancellation_reason = cancellation_reason

        booking.save(
            update_fields=[
                "status",
                "cancellation_reason"
            ]
        )

        # ==============================================
        # ELIGIBLE REFUND
        # ==============================================

        if refund_allowed and refund_amount > Decimal("0.00"):

            # ------------------------------------------
            # Get/Create User Wallet
            # ------------------------------------------

            wallet, created = UserWallet.objects.get_or_create(
                user=request.user
            )

            # Lock wallet
            wallet = UserWallet.objects.select_for_update().get(
                id=wallet.id
            )

            # ------------------------------------------
            # Add refund to wallet
            # ------------------------------------------

            wallet.balance = (
                wallet.balance +
                refund_amount
            )

            wallet.save(
                update_fields=[
                    "balance",
                    "updated_at"
                ]
            )

            # ------------------------------------------
            # Create wallet transaction
            # ------------------------------------------

            WalletTransaction.objects.create(

                user=request.user,
                 wallet=wallet,

                booking=booking,

                payment=advance_payment,

                amount=refund_amount,

                transaction_type="refund",

                status="completed",

                description=(
                    f"Refund for cancelled booking "
                    f"#{booking.id}"
                )
            )

            # ------------------------------------------
            # Payment becomes refunded
            # ------------------------------------------

            advance_payment.status = "refunded"

            advance_payment.save(
                update_fields=["status"]
            )

        # ==============================================
        # NO REFUND AFTER 24 HOURS
        # ==============================================

        else:

            # No wallet transaction

            # Payment remains paid

            wallet = UserWallet.objects.filter(
                user=request.user
            ).first()

    # ==================================================
    # 13. MESSAGE
    # ==================================================

    if refund_allowed:

        message = (
            "Booking cancelled successfully. "
            "Refund credited to your wallet. "
            "The platform fee is non-refundable."
        )

    else:

        message = (
            "Booking cancelled successfully. "
            "The 24-hour refund period has expired, "
            "so no refund is available."
        )

    # ==================================================
    # 14. RESPONSE DATA
    # ==================================================

    data = {
        "booking_id": booking.id,

        "booking_status": booking.status,

        "photographer_status": original_status,

        "booking_created_at": booking.created_at,

        "refund_deadline": refund_deadline,
        "cancellation_reason": booking.cancellation_reason,

        "hours_remaining": round(
            hours_remaining,
            2
        ),

        "advance_paid": advance_paid,

        "platform_fee": platform_fee,

        "refund_amount": refund_amount,

        "refund_status": refund_status,

        "wallet_balance": (
            wallet.balance
            if refund_allowed and wallet
            else None
        )
    }

    serializer = CancelBookingSerializer(
        data=data
    )

    serializer.is_valid(
        raise_exception=True
    )

    return Response(
        {
            "success": True,
            "message": message,
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="post",
    request_body=ForgotPasswordSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
def forgot_password(request):

    serializer = ForgotPasswordSerializer(data=request.data)

    if serializer.is_valid():

        email = serializer.validated_data["email"].strip().lower()

        # Check whether user exists
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "error": "No account found with this email."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Remove old OTP
        PasswordResetOTP.objects.filter(
            email=email
        ).delete()

        # Save new OTP
        PasswordResetOTP.objects.create(
            email=email,
            otp=otp,
            created_at=timezone.now()
        )

        # Send OTP
        send_mail(
            subject="Snapshire - Password Reset",
            message=f"""
Hello,

We received a request to reset your Snapshire account password.

Your verification code is: {otp}

This code is valid for 5 minutes. Please do not share this code with anyone.

If you did not request a password reset, you may safely disregard this email.

Regards,
Snapshire Team
Photography Booking Platform
""",
            from_email=None,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "OTP sent successfully. Please check your email."
            },
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="post",
    request_body=ResetPasswordSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
def reset_password(request):

    serializer = ResetPasswordSerializer(data=request.data)

    if serializer.is_valid():

        email = serializer.validated_data["email"].strip().lower()
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        try:
            otp_record = PasswordResetOTP.objects.get(
                email=email
            )
        except PasswordResetOTP.DoesNotExist:

            return Response(
                {
                    "error": "OTP not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Check OTP expiry
        if timezone.now() > otp_record.created_at + timedelta(minutes=5):

            otp_record.delete()

            return Response(
                {
                    "error": "OTP has expired."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check OTP
        if otp_record.otp != otp:

            return Response(
                {
                    "error": "Invalid OTP."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:

            return Response(
                {
                    "error": "User not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Update password
        user.password = make_password(new_password)
        user.save()

        # Delete OTP after successful reset
        otp_record.delete()

        return Response(
            {
                "message": "Password reset successful."
            },
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


from decimal import Decimal

import razorpay

from django.conf import settings

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from .models import Booking, Payment
from .serializers import CreatePaymentSerializer


@swagger_auto_schema(
    method="post",
    request_body=CreatePaymentSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def create_razorpay_order(request):

    serializer = CreatePaymentSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking_id = serializer.validated_data["booking_id"]

    # -----------------------------------------
    # GET USER'S BOOKING
    # -----------------------------------------

    try:
        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------------
    # CHECK BOOKING STATUS
    # -----------------------------------------

    if booking.status != "payment_pending":
        return Response(
            {
                "success": False,
                "message": "This booking is not available for payment."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # CHECK EXISTING ADVANCE PAYMENT
    # -----------------------------------------

    existing_payment = Payment.objects.filter(
        booking=booking,
        payment_type="advance",
        status="created"
    ).first()

    if existing_payment:

        return Response(
            {
                "success": True,
                "message": "Payment order already exists.",
                "data": {
                    "booking_id": booking.id,
                    "payment_id": existing_payment.id,
                    "payment_type": existing_payment.payment_type,
                    "amount": existing_payment.amount,
                    "currency": "INR",
                    "razorpay_order_id": existing_payment.razorpay_order_id,
                    "razorpay_key_id": settings.RAZORPAY_KEY_ID
                }
            },
            status=status.HTTP_200_OK
        )

    # -----------------------------------------
    # ADVANCE AMOUNT
    # -----------------------------------------

    amount = Decimal(str(booking.advance_amount))

    if amount <= 0:
        return Response(
            {
                "success": False,
                "message": "Invalid advance payment amount."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Razorpay requires amount in paise
    amount_paise = int(amount * Decimal("100"))

    # -----------------------------------------
    # RAZORPAY CLIENT
    # -----------------------------------------

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # -----------------------------------------
    # CREATE RAZORPAY ORDER
    # -----------------------------------------

    try:

        razorpay_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"booking_{booking.id}"
            }
        )

    except Exception:
        return Response(
            {
                "success": False,
                "message": "Unable to create Razorpay order."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # -----------------------------------------
    # SAVE PAYMENT
    # -----------------------------------------

    payment = Payment.objects.create(
        booking=booking,
        payment_type="advance",
        amount=amount,
        razorpay_order_id=razorpay_order["id"],
        status="created"
    )

    # -----------------------------------------
    # RESPONSE
    # -----------------------------------------

    return Response(
        {
            "success": True,
            "message": "Razorpay order created successfully.",
            "data": {
                "booking_id": booking.id,
                "payment_id": payment.id,
                "payment_type": payment.payment_type,
                "amount": payment.amount,
                "currency": "INR",
                "razorpay_order_id": payment.razorpay_order_id,
                "razorpay_key_id": settings.RAZORPAY_KEY_ID
            }
        },
        status=status.HTTP_201_CREATED
    )


from decimal import Decimal

import razorpay

from django.conf import settings

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from .models import Payment
from .serializers import VerifyPaymentSerializer


@swagger_auto_schema(
    method="post",
    request_body=VerifyPaymentSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def verify_razorpay_payment(request):

    # -----------------------------------------
    # VALIDATE REQUEST DATA
    # -----------------------------------------

    serializer = VerifyPaymentSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    razorpay_payment_id = serializer.validated_data[
        "razorpay_payment_id"
    ]

    razorpay_order_id = serializer.validated_data[
        "razorpay_order_id"
    ]

    razorpay_signature = serializer.validated_data[
        "razorpay_signature"
    ]

    # -----------------------------------------
    # GET PAYMENT RECORD
    # -----------------------------------------

    try:

        payment = Payment.objects.select_related(
            "booking"
        ).get(
            razorpay_order_id=razorpay_order_id,
            booking__user=request.user
        )

    except Payment.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Payment record not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------------
    # ALREADY PAID
    # -----------------------------------------

    if payment.status == "paid":

        booking = payment.booking

        return Response(
            {
                "success": True,
                "message": "Payment already verified.",
                "data": {
                    "payment_id": payment.id,
                    "booking_id": booking.id,
                    "payment_type": payment.payment_type,
                    "amount": str(payment.amount),
                    "payment_status": payment.status,
                    "booking_status": booking.status
                }
            },
            status=status.HTTP_200_OK
        )

    # -----------------------------------------
    # CREATE RAZORPAY CLIENT
    # -----------------------------------------

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # -----------------------------------------
    # STEP 1: VERIFY SIGNATURE
    # -----------------------------------------

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_payment_id":
                    razorpay_payment_id,

                "razorpay_order_id":
                    payment.razorpay_order_id,

                "razorpay_signature":
                    razorpay_signature
            }
        )

    except razorpay.errors.SignatureVerificationError:

        return Response(
            {
                "success": False,
                "message": "Payment signature verification failed."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # STEP 2: FETCH PAYMENT FROM RAZORPAY
    # -----------------------------------------

    try:

        razorpay_payment = client.payment.fetch(
            razorpay_payment_id
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message": "Unable to fetch Razorpay payment.",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # -----------------------------------------
    # STEP 3: CHECK ORDER ID
    # -----------------------------------------

    if (
        razorpay_payment.get("order_id")
        != payment.razorpay_order_id
    ):

        return Response(
            {
                "success": False,
                "message": "Payment does not belong to this order."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # STEP 4: CHECK AMOUNT
    # -----------------------------------------

    expected_amount = int(
        Decimal(str(payment.amount)) * Decimal("100")
    )

    razorpay_amount = razorpay_payment.get("amount")

    if razorpay_amount != expected_amount:

        return Response(
            {
                "success": False,
                "message": "Payment amount mismatch."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # STEP 5: CHECK PAYMENT STATUS
    # -----------------------------------------

    if razorpay_payment.get("status") != "captured":

        return Response(
            {
                "success": False,
                "message": "Payment has not been captured."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------------
    # STEP 6: SAVE PAYMENT
    # -----------------------------------------

    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "paid"

    payment.save(
        update_fields=[
            "razorpay_payment_id",
            "razorpay_signature",
            "status"
        ]
    )

    # -----------------------------------------
    # STEP 7: UPDATE BOOKING STATUS
    # -----------------------------------------

    booking = payment.booking

    if payment.payment_type == "advance":

        # Advance payment completed.
        # Send booking to photographer.
        booking.status = "waiting_photographer"

        booking.save(
            update_fields=["status"]
        )

    elif payment.payment_type == "balance":

        # Balance payment happens after work completion.
        # Booking must remain completed.
        booking.status = "completed"

        booking.save(
            update_fields=["status"]
        )

    # -----------------------------------------
    # STEP 8: SUCCESS RESPONSE
    # -----------------------------------------

    return Response(
        {
            "success": True,
            "message": "Payment verified successfully.",
            "data": {
                "payment_id": payment.id,
                "booking_id": booking.id,
                "payment_type": payment.payment_type,
                "amount": str(payment.amount),
                "payment_status": payment.status,
                "booking_status": booking.status
            }
        },
        status=status.HTTP_200_OK
    )
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def booking_payment_details(request, booking_id):

    try:

        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = BookingPaymentDetailsSerializer(booking)

    # Photographer has not completed work
    if booking.status != "completed":

        return Response(
            {
                "success": True,
                "message": (
                    "Balance payment is not available yet. "
                    "The photographer has not completed the work."
                ),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    # Photographer completed work
    return Response(
        {
            "success": True,
            "message": "Work completed. Balance payment is available.",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="post",
    request_body=CreateBalancePaymentSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def create_balance_payment(request):

    # -------------------------------
    # 1. VALIDATE DATA
    # -------------------------------

    serializer = CreateBalancePaymentSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking_id = serializer.validated_data["booking_id"]

    # -------------------------------
    # 2. GET USER BOOKING
    # -------------------------------

    try:

        booking = Booking.objects.get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -------------------------------
    # 3. CHECK WORK COMPLETION
    # -------------------------------

    if booking.status != "completed":

        return Response(
            {
                "success": False,
                "message": (
                    "Balance payment is available only "
                    "after the photographer completes the work."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -------------------------------
    # 4. CHECK ADVANCE PAYMENT
    # -------------------------------

    advance_payment = Payment.objects.filter(
        booking=booking,
        payment_type="advance",
        status="paid"
    ).exists()

    if not advance_payment:

        return Response(
            {
                "success": False,
                "message": "Advance payment is not completed."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -------------------------------
    # 5. CHECK BALANCE ALREADY PAID
    # -------------------------------

    balance_paid = Payment.objects.filter(
        booking=booking,
        payment_type="balance",
        status="paid"
    ).first()

    if balance_paid:

        return Response(
            {
                "success": False,
                "message": "Balance payment already completed."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -------------------------------
    # 6. CHECK EXISTING ORDER
    # -------------------------------

    existing_payment = Payment.objects.filter(
        booking=booking,
        payment_type="balance",
        status="created"
    ).first()

    if existing_payment:

        return Response(
            {
                "success": True,
                "message": "Balance payment order already exists.",
                "data": {
                    "booking_id": booking.id,
                    "payment_id": existing_payment.id,
                    "payment_type": "balance",
                    "amount": str(existing_payment.amount),
                    "currency": "INR",
                    "razorpay_order_id":
                        existing_payment.razorpay_order_id,
                    "razorpay_key_id":
                        settings.RAZORPAY_KEY_ID
                }
            },
            status=status.HTTP_200_OK
        )

    # -------------------------------
    # 7. BALANCE AMOUNT
    # -------------------------------

    amount = booking.balance_amount

    amount_paise = int(
        Decimal(str(amount)) * 100
    )

    # -------------------------------
    # 8. RAZORPAY CLIENT
    # -------------------------------

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # -------------------------------
    # 9. CREATE ORDER
    # -------------------------------

    try:

        razorpay_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"balance_booking_{booking.id}"
            }
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message":
                    "Unable to create balance payment order.",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # -------------------------------
    # 10. CREATE PAYMENT RECORD
    # -------------------------------

    payment = Payment.objects.create(
        booking=booking,
        payment_type="balance",
        amount=amount,
        razorpay_order_id=razorpay_order["id"],
        status="created"
    )

    # -------------------------------
    # 11. RESPONSE
    # -------------------------------

    return Response(
        {
            "success": True,
            "message":
                "Balance payment order created successfully.",

            "data": {

                "booking_id": booking.id,

                "payment_id": payment.id,

                "payment_type": payment.payment_type,

                "amount": str(payment.amount),

                "currency": "INR",

                "razorpay_order_id":
                    payment.razorpay_order_id,

                "razorpay_key_id":
                    settings.RAZORPAY_KEY_ID
            }
        },
        status=status.HTTP_201_CREATED
    )



@swagger_auto_schema(
    method="post",
    request_body=CreateFeedbackSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser, MultiPartParser])
def create_photographer_feedback(request, booking_id):

    
    #  GET USER'S BOOKING
    

    try:
        booking = Booking.objects.select_related(
            "photographer",
            "photographer__user"
        ).get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    
    #  CHECK PHOTOGRAPHER
    

    if not booking.photographer:
        return Response(
            {
                "success": False,
                "message": "No photographer is assigned to this booking."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 3. CHECK WORK COMPLETED
    # -----------------------------------

    if booking.status != "completed":
        return Response(
            {
                "success": False,
                "message": (
                    "You can give feedback only after "
                    "the photographer completes the work."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 4. CHECK ALREADY GIVEN FEEDBACK
    # -----------------------------------

    if Feedback.objects.filter(
        booking=booking,
        user=request.user
    ).exists():

        return Response(
            {
                "success": False,
                "message": (
                    "You have already submitted feedback "
                    "for this booking."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 5. VALIDATE REQUEST DATA
    # -----------------------------------

    serializer = CreateFeedbackSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 6. CREATE FEEDBACK
    # -----------------------------------

    feedback = Feedback.objects.create(
        booking=booking,
        user=request.user,
        photographer=booking.photographer,
        rating=serializer.validated_data["rating"],
        comment=serializer.validated_data["comment"]
    )

    # -----------------------------------
    # 7. RESPONSE
    # -----------------------------------

    return Response(
        {
            "success": True,
            "message": "Feedback submitted successfully.",
            "data": {
                "feedback_id": feedback.id,
                "booking_id": booking.id,
                "photographer_id": booking.photographer.id,
                "photographer_name": (
                    f"{booking.photographer.user.first_name} "
                    f"{booking.photographer.user.last_name}"
                ).strip(),
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at
            }
        },
        status=status.HTTP_201_CREATED
    )


@swagger_auto_schema(
    method="get",
    responses={
        200: UserFeedbackListSerializer(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_feedback_list(request):

    feedbacks = Feedback.objects.filter(
        user=request.user
    ).select_related(
        "booking",
        "photographer",
        "photographer__user"
    ).order_by("-created_at")

    serializer = UserFeedbackListSerializer(
        feedbacks,
        many=True
    )

    return Response(
        {
            "success": True,
            "count": feedbacks.count(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={
        200: UserWalletSerializer
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_wallet(request):

    wallet, created = UserWallet.objects.get_or_create(
        user=request.user
    )

    serializer = UserWalletSerializer(wallet)

    return Response(
        {
            "success": True,
            "message": "Wallet retrieved successfully.",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )

from rest_framework.pagination import PageNumberPagination


class WalletTransactionPagination(PageNumberPagination):

    page_size = 10

    page_size_query_param = "page_size"

    max_page_size = 50

@swagger_auto_schema(
    method="get",
    responses={
        200: WalletTransactionSerializer(many=True)
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_transactions(request):

    # ---------------------------------------------
    # 1. Get user's wallet
    # ---------------------------------------------

    wallet = UserWallet.objects.filter(
        user=request.user
    ).first()

    # ---------------------------------------------
    # 2. Wallet does not exist
    # ---------------------------------------------

    if not wallet:

        return Response(
            {
                "success": True,
                "message": "Wallet has no transactions.",
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            },
            status=status.HTTP_200_OK
        )

    # ---------------------------------------------
    # 3. Get only this wallet's transactions
    # ---------------------------------------------

    transactions = WalletTransaction.objects.filter(
        wallet=wallet,
        user=request.user
    ).select_related(
        "booking",
        "payment"
    ).order_by(
        "-created_at"
    )

    # ---------------------------------------------
    # 4. Pagination
    # ---------------------------------------------

    paginator = PageNumberPagination()

    paginator.page_size = 10

    result_page = paginator.paginate_queryset(
        transactions,
        request
    )

    # ---------------------------------------------
    # 5. Serialize
    # ---------------------------------------------

    serializer = WalletTransactionSerializer(
        result_page,
        many=True
    )

    # ---------------------------------------------
    # 6. Response
    # ---------------------------------------------

    return Response(
        {
            "success": True,
            "message": (
                "Wallet transactions retrieved successfully."
            ),
            "count": transactions.count(),
            "next": paginator.get_next_link(),
            "previous": paginator.get_previous_link(),
            "results": serializer.data
        },
        status=status.HTTP_200_OK
    )

def check_photographer_availability(
    photographer,
    selected_date,
    session,
    exclude_booking_id=None
):

    # ---------------------------------------------
    # 1. Weekly availability
    # ---------------------------------------------

    weekday = selected_date.weekday()

    weekly = WeeklyAvailability.objects.filter(
        photographer=photographer,
        weekday=weekday
    ).first()

    if not weekly:
        return False

    # ---------------------------------------------
    # 2. Check morning / afternoon
    # ---------------------------------------------

    if session == "morning":

        available = weekly.morning

    elif session == "afternoon":

        available = weekly.afternoon

    else:

        return False

    if not available:
        return False

    # ---------------------------------------------
    # 3. Check exceptions
    # ---------------------------------------------

    exceptions = AvailabilityException.objects.filter(
        photographer=photographer,
        date=selected_date
    )

    for exception in exceptions:

        if exception.session == "full_day":
            return False

        if exception.session == session:
            return False

    # ---------------------------------------------
    # 4. Check existing bookings
    # ---------------------------------------------

    ACTIVE_STATUS = [
        "payment_pending",
        "waiting_photographer",
        "photographer_accepted",
        "waiting_admin",
        "confirmed",
        "completed",
    ]

    bookings = Booking.objects.filter(
        photographer=photographer,
        date=selected_date,
        session=session,
        status__in=ACTIVE_STATUS
    )

    # Don't count the booking being rescheduled
    if exclude_booking_id:

        bookings = bookings.exclude(
            id=exclude_booking_id
        )

    if bookings.exists():
        return False

    return True


# =================================================
# REQUEST RESCHEDULE
# =================================================

@swagger_auto_schema(
    method="post",
    request_body=RescheduleRequestSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def request_reschedule(request):

    # =================================================
    # 1. Validate request
    # =================================================

    serializer = RescheduleRequestSerializer(
        data=request.data
    )

    if not serializer.is_valid():

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking_id = serializer.validated_data["booking_id"]

    new_date = serializer.validated_data["new_date"]

    new_time = serializer.validated_data["new_time"]

    new_session = serializer.validated_data["new_session"]

    description = serializer.validated_data["description"]

    # =================================================
    # 2. Get user's booking
    # =================================================

    try:

        booking = Booking.objects.select_related(
            "photographer",
            "photographer__user"
        ).get(
            id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    photographer = booking.photographer

    # =================================================
    # 3. Check booking status
    # =================================================

    ALLOWED_STATUS = [
        "photographer_accepted",
        "confirmed",
    ]

    if booking.status not in ALLOWED_STATUS:

        return Response(
            {
                "success": False,
                "message": (
                    "This booking cannot be rescheduled "
                    "because of its current status."
                ),
                "booking_status": booking.status
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 4. Calculate original booking datetime
    # =================================================

    booking_datetime = timezone.make_aware(
        datetime.combine(
            booking.date,
            booking.shoot_time
        ),
        timezone.get_current_timezone()
    )

    # =================================================
    # 5. Check 5-hour deadline
    # =================================================

    reschedule_deadline = (
        booking_datetime - timedelta(hours=5)
    )

    now = timezone.now()

    if now >= reschedule_deadline:

        return Response(
            {
                "success": False,
                "message": (
                    "Rescheduling is not possible. "
                    "You must request rescheduling "
                    "at least 5 hours before the "
                    "booked time."
                ),
                "booking_date": booking.date,
                "booking_time": booking.shoot_time,
                "reschedule_deadline": reschedule_deadline
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 6. Check new datetime
    # =================================================

    new_datetime = timezone.make_aware(
        datetime.combine(
            new_date,
            new_time
        ),
        timezone.get_current_timezone()
    )

    if new_datetime <= now:

        return Response(
            {
                "success": False,
                "message": (
                    "The new date and time must "
                    "be in the future."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 7. New date/time/session cannot be same
    # =================================================

    if (
        new_date == booking.date
        and
        new_time == booking.shoot_time
        and
        new_session == booking.session
    ):

        return Response(
            {
                "success": False,
                "message": (
                    "The new date, time and session "
                    "must be different from the "
                    "current booking."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 8. Check pending request
    # =================================================

    pending_request = RescheduleRequest.objects.filter(
        booking=booking,
        status="pending"
    ).exists()

    if pending_request:

        return Response(
            {
                "success": False,
                "message": (
                    "A rescheduling request is already "
                    "pending for this booking."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 9. Check photographer availability
    # =================================================

    available = check_photographer_availability(
        photographer=photographer,
        selected_date=new_date,
        session=new_session,
        exclude_booking_id=booking.id
    )

    if not available:

        return Response(
            {
                "success": False,
                "message": (
                    "Photographer is not available "
                    "for the selected date and session."
                ),
                "new_date": new_date,
                "new_time": new_time,
                "new_session": new_session
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # =================================================
    # 10. Create reschedule request
    # =================================================

    reschedule = RescheduleRequest.objects.create(
        booking=booking,
        user=request.user,
        photographer=photographer,

        old_date=booking.date,
        old_time=booking.shoot_time,

        new_date=new_date,
        new_time=new_time,
        new_session=new_session,

        description=description,

        status="pending"
    )

    # =================================================
    # 11. Response
    # =================================================

    return Response(
        {
            "success": True,
            "message": (
                "Rescheduling request submitted "
                "successfully. Waiting for "
                "photographer approval."
            ),
            "data": {

                "reschedule_id": reschedule.id,

                "booking_id": booking.id,

                "photographer_id": photographer.id,

                "photographer_name": (
                    photographer.user.username
                ),

                "old_date": reschedule.old_date,

                "old_time": reschedule.old_time,

                "old_session": booking.session,

                "new_date": reschedule.new_date,

                "new_time": reschedule.new_time,

                "new_session": reschedule.new_session,

                "description": reschedule.description,

                "status": reschedule.status,

                "reschedule_deadline": (
                    reschedule_deadline
                ),

                "created_at": (
                    reschedule.created_at
                )
            }
        },
        status=status.HTTP_201_CREATED
    )

from rest_framework.views import APIView


class GoogleLoginView(APIView):

    @swagger_auto_schema(request_body=GoogleLoginSerializer)
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            google_user = id_token.verify_oauth2_token(
                serializer.validated_data["id_token"],
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response({
                "success": False,
                "message": "Invalid Google ID token."
            }, status=status.HTTP_400_BAD_REQUEST)

        email = (google_user.get("email") or "").strip()

        if not email or google_user.get("email_verified") is not True:
            return Response({
                "success": False,
                "message": "A verified Google email is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()

        if user:
            # Block photographer accounts
            if PhotographerProfile.objects.filter(user=user).exists():
                return Response({
                    "success": False,
                    "message": (
                        "This email belongs to a photographer. "
                        "Please use Photographer Login."
                    )
                }, status=status.HTTP_403_FORBIDDEN)

            # Existing accounts must already have a UserProfile
            profile = UserProfile.objects.filter(user=user).first()

            if not profile:
                return Response({
                    "success": False,
                    "message": "User profile not found. Please contact support."
                }, status=status.HTTP_403_FORBIDDEN)

        else:
            # Register a new normal user
            user = User.objects.create_user(
                username=email,
                email=email
            )

            profile = UserProfile.objects.create(
                user=user,
                first_name=google_user.get("given_name", ""),
                last_name=google_user.get("family_name", "")
            )

        # Fill names only when they are empty
        changed = False

        if not profile.first_name and google_user.get("given_name"):
            profile.first_name = google_user["given_name"]
            changed = True

        if not profile.last_name and google_user.get("family_name"):
            profile.last_name = google_user["family_name"]
            changed = True

        if changed:
            profile.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Google login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": profile.first_name,
                "last_name": profile.last_name
            }
        }, status=status.HTTP_200_OK)
