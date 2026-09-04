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
from .serializers import PhotographerViewSerializer,PhotographerDetailSerializer,PhotographerFilterSerializer,CreatePaymentSerializer,VerifyPaymentSerializer
from .models import Booking
from .serializers import BookingSerializer,UserBookingStatusSerializer,VerifyOTPSerializer
from decimal import Decimal
from .models import Notification
from .serializers import NotificationSerializer,ForgotPasswordSerializer,ResetPasswordSerializer
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

from django.conf import settings

from .models import Booking, Payment




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

    hours = serializer.validated_data["hours"]

    try:
        charge = PhotographerCharge.objects.get(
            photographer=photographer,
            hours=hours
        )
    except PhotographerCharge.DoesNotExist:
        return Response(
            {
                "error": (
                    f"Price for {hours} hour(s) "
                    "is not available for this photographer."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Photographer's charge for selected hours
    photographer_amount = charge.amount

    # Fixed platform fee
    fee = PlatformFee.objects.first()

    if not fee:
        return Response(
            {
                "success": False,
                "message": "Platform fee has not been configured by admin."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    platform_fee = fee.amount

     # Total booking amount
    total_amount = (
        photographer_amount + platform_fee
    )

    # 50% advance payment
    advance_amount = (
        total_amount / Decimal("2")
    )

    # Remaining 50%
    balance_amount = (
        total_amount - advance_amount
    )
    

    

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


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_booking(request, booking_id):

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

    # Cancellation allowed only before payment
    if booking.status != "payment_pending":
        return Response(
            {
                "success": False,
                "message": "Booking cannot be cancelled at this stage."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = "cancelled"
    booking.save(update_fields=["status"])

    return Response(
        {
            "success": True,
            "message": "Booking cancelled successfully."
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


@swagger_auto_schema(
    method="post",
    request_body=CreatePaymentSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def create_razorpay_order(request):

    serializer = CreatePaymentSerializer(
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

    # Get booking belonging to logged-in user
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

    # Booking must be waiting for payment
    if booking.status != "payment_pending":
        return Response(
            {
                "success": False,
                "message": "This booking is not available for payment."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check whether an unpaid advance payment already exists
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

    # Advance amount = 50%
    amount = booking.advance_amount

    # Convert rupees to paise
    amount_paise = int(amount * 100)

    # Razorpay client
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Create Razorpay order
    try:

        razorpay_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"booking_{booking.id}"
            }
        )

    except Exception as e:

        return Response(
            {
                "success": False,
                "message": "Unable to create Razorpay order.",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Save payment in database
    payment = Payment.objects.create(
        booking=booking,
        payment_type="advance",
        amount=amount,
        razorpay_order_id=razorpay_order["id"],
        status="created"
    )

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
@swagger_auto_schema(
    method="post",
    request_body=VerifyPaymentSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def verify_razorpay_payment(request):

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

    # Find the payment belonging to the logged-in user
    try:

        payment = Payment.objects.get(
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

    # If payment is already paid
    if payment.status == "paid":

        return Response(
            {
                "success": True,
                "message": "Payment already verified.",
                "data": {
                    "payment_id": payment.id,
                    "booking_id": payment.booking.id,
                    "payment_status": payment.status,
                    "booking_status": payment.booking.status
                }
            },
            status=status.HTTP_200_OK
        )

    # Create Razorpay client
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Verify Razorpay signature
    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_signature": razorpay_signature
            }
        )

    except razorpay.errors.SignatureVerificationError:

        payment.status = "failed"

        payment.save(
            update_fields=["status"]
        )

        return Response(
            {
                "success": False,
                "message": "Payment verification failed."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # Signature is valid
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

    # Update booking
    booking = payment.booking

    booking.status = "waiting_photographer"

    booking.save(
        update_fields=["status"]
    )

    return Response(
        {
            "success": True,
            "message": "Payment verified successfully.",
            "data": {
                "payment_id": payment.id,
                "booking_id": booking.id,
                "payment_type": payment.payment_type,
                "amount": payment.amount,
                "payment_status": payment.status,
                "booking_status": booking.status
            }
        },
        status=status.HTTP_200_OK
    )