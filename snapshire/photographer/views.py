import os
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .serializers import SignupSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import SignupSerializer, LoginSerializer,UpdatePhotographerProfileSerializer,PhotographerProfileSerializer,PhotographerDashboardSerializer,PhotographerWalletTransactionSerializer
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from .serializers import VerificationSerializer
from user.models import Notification,RescheduleRequest
from user.serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import WeeklyAvailability, AvailabilityException,PhotographerProfile,PhotographerCharge,PhotographerWalletTransaction,PhotographerWallet,PhotographerProfile, PhotographerPasswordResetOTP
from .serializers import WeeklyAvailabilitySerializer,AvailabilityExceptionSerializer,RejectBookingSerializer,PhotographerMyBookingSerializer,UpdatePhotographerChargeSerializer, PhotographerWalletSerializer,PhotographerGoogleLoginSerializer, PhotographerForgotPasswordSerializer,PhotographerResetPasswordSerializer
from datetime import date, timedelta
import random
from .serializers import  PhotographerVerifyOTPSerializer,PhotographerChargeSerializer,PhotographerBookingRequestSerializer,PhotographerRescheduleRequestSerializer,CreateVerificationOrderSerializer

from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from user.models import EmailOTP,Booking,Payment
from .serializers import SignupSerializer
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from .serializers import UpdateWorkStatusSerializer
from user.models import Booking,UserProfile
from django.db.models import Sum
from django.db import transaction
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import (
    PhotographerWallet,
    PhotographerWalletTransaction,
    
)
from rest_framework.parsers import FormParser

from admin.models import VerificationPlan
from .serializers import VerificationSerializer
from decimal import Decimal
from django.conf import settings
from django.db import transaction


import razorpay


from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from admin.models import VerificationPlan
from .models import VerificationPayment
from .serializers import CreateVerificationOrderSerializer

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
#             {
#                 "message": "Photographer registered successfully."
#             },
#             status=status.HTTP_201_CREATED
#         )

#     return Response(
#         serializer.errors,
#         status=status.HTTP_400_BAD_REQUEST
#     )

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

        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"].lower()
        password = serializer.validated_data["password"]

        otp = str(random.randint(100000, 999999))

        EmailOTP.objects.filter(email=email).delete()

        EmailOTP.objects.create(
            username=username,
            email=email,
            password=password,
            otp=otp,
            created_at=timezone.now()
        )

        send_mail(
            "Snapshire - OTP Verification",
        f"""
        Hello,

        Thank you for using Snapshire.

        Your One-Time Password (OTP) for email verification is:

            {otp}

        This OTP is required to verify your email address and complete your registration.

    Important:
    - This OTP is valid for 5 minutes.
    - Do not share this OTP with anyone.
    - Snapshire will never ask you to share your OTP.
    - If you did not request this OTP, you can safely ignore this email.

    Regards
    Snapshire Team
""",
None,
[email],
)

        return Response(
            {
                "message": "OTP sent successfully."
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

    




# @swagger_auto_schema(
#     method="post",
#     request_body=VerificationSerializer,
# )
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# @parser_classes([FormParser])
# def verification(request):
#     response = check_photographer_verification(request)
#     if response:
#         return response

#     serializer = VerificationSerializer(data=request.data)

#     if serializer.is_valid():

#         profile = request.user.photographer_profile
#         plan = serializer.validated_data["plan_mode"]

#         # Prevent selecting the same plan again
#         if profile.plan_mode == plan:
#             return Response(
#                 {
#                     "message": f"You are already using the {plan.capitalize()} plan."
#                 },
#                 status=status.HTTP_200_OK
#             )

#         if plan == "free":

#             profile.plan_mode = "free"
#             profile.save()

#             return Response(
#                 {
#                     "message": "Free plan activated successfully.",
#                     "plan_mode": profile.plan_mode
#                 },
#                 status=status.HTTP_200_OK
#             )

#         if plan == "gold":

#             return Response(
#                 {
#                     "message": "Gold plan requires payment. Payment integration will be available soon."
#                 },
#                 status=status.HTTP_200_OK
#             )

#         if plan == "platinum":

#             return Response(
#                 {
#                     "message": "Platinum plan requires payment. Payment integration will be available soon."
#                 },
#                 status=status.HTTP_200_OK
#             )

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method="post",
    request_body=VerificationSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def verification(request):
    response = check_photographer_verification(request)
    if response:
        return response

    serializer = VerificationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    profile = request.user.photographer_profile
    plan = serializer.validated_data["plan_mode"]

    # Prevent selecting the same plan again
    if profile.plan_mode == plan:
        return Response(
            {
                "message": f"You are already using the {plan.capitalize()} plan."
            },
            status=status.HTTP_200_OK,
        )

    # Activate the free plan
    if plan == "free":
        profile.plan_mode = "free"
        profile.save(update_fields=["plan_mode"])

        return Response(
            {
                "message": "Free plan activated successfully.",
                "plan_mode": profile.plan_mode,
            },
            status=status.HTTP_200_OK,
        )

    # Get the admin-configured charge for Gold or Platinum
    try:
        verification_plan = VerificationPlan.objects.get(
            plan_name=plan,
            is_active=True,
        )
    except VerificationPlan.DoesNotExist:
        return Response(
            {
                "error": f"The {plan.capitalize()} plan is currently unavailable."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "message": f"The {plan.capitalize()} plan requires payment.",
            "plan_mode": plan,
            "verification_charge": str(
                verification_plan.verification_charge
            ),
            "payment_required": True,
        },
        status=status.HTTP_200_OK,
    )
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
@parser_classes([FormParser])
def create_weekly_availability(request):
    response = check_photographer_verification(request)
    if response:
        return response
     

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
    response = check_photographer_verification(request)
    if response:
        return response

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
@parser_classes([FormParser])
def update_weekly_availability(request, availability_id):
    response = check_photographer_verification(request)
    if response:
        return response

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
    response = check_photographer_verification(request)
    if response:
        return response

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
@parser_classes([FormParser])
def create_availability_exception(request):
    response = check_photographer_verification(request)
    if response:
        return response

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
    response = check_photographer_verification(request)
    if response:
        return response

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
    response = check_photographer_verification(request)
    if response:
        return response

    

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


@swagger_auto_schema(
    method="post",
    request_body= PhotographerVerifyOTPSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
def verify_otp(request):

    serializer = PhotographerVerifyOTPSerializer(data=request.data)

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
                    "error": "OTP expired."
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

        # Create User
        user = User.objects.create_user(

            username=otp_record.username,

            email=otp_record.email,

            password=otp_record.password

)

            

     

        # Create Photographer Profile
        PhotographerProfile.objects.create(
            user=user
        )

        # Delete OTP record
        otp_record.delete()

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
    request_body=PhotographerChargeSerializer
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def create_photographer_charge(request):
    response = check_photographer_verification(request)
    if response:
        return response

    try:
        photographer = PhotographerProfile.objects.get(
            user=request.user
        )
    except PhotographerProfile.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Photographer profile not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = PhotographerChargeSerializer(
        data=request.data
    )

    if serializer.is_valid():

        hours = serializer.validated_data["hours"]

        # Check whether this duration already exists
        if PhotographerCharge.objects.filter(
            photographer=photographer,
            hours=hours
        ).exists():

            return Response(
                {
                    "success": False,
                    "message": f"Charge for {hours} hour(s) already exists."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(
            photographer=photographer
        )

        return Response(
            {
                "success": True,
                "message": "Photographer charge added successfully.",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    return Response(
        {
            "success": False,
            "errors": serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="get",
    responses={200: PhotographerBookingRequestSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_booking_requests(request):
    response = check_photographer_verification(request)
    if response:
        return response

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    bookings = Booking.objects.filter(
        photographer=photographer,
        status="waiting_photographer"
    ).select_related("user")

    serializer = PhotographerBookingRequestSerializer(
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


@swagger_auto_schema(
    method="post"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_booking_request(request, booking_id):
    response = check_photographer_verification(request)
    if response:
        return response

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    try:
        booking = Booking.objects.get(
            id=booking_id,
            photographer=photographer
        )
    except Booking.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Booking request not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if booking.status != "waiting_photographer":
        return Response(
            {
                "success": False,
                "message": "This booking request is no longer available."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = "photographer_accepted"
    booking.save(update_fields=["status"])

    return Response(
        {
            "success": True,
            "message": "Booking request accepted successfully.",
            "data": {
                "booking_id": booking.id,
                "status": booking.status
            }
        },
        status=status.HTTP_200_OK
    )

@swagger_auto_schema(
    method="post",
    request_body=RejectBookingSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
@permission_classes([IsAuthenticated])
def reject_booking_request(request, booking_id):

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    try:
        booking = Booking.objects.get(
            id=booking_id,
            photographer=photographer
        )
    except Booking.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Booking request not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    if booking.status != "waiting_photographer":
        return Response(
            {
                "success": False,
                "message": "This booking request is no longer available."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = RejectBookingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    reject_reason = serializer.validated_data["reject_reason"]

    # Change status and save rejection reason
    booking.status = "photographer_rejected"
    booking.reject_reason = reject_reason

    booking.save(
        update_fields=[
            "status",
            "reject_reason"
        ]
    )

    return Response(
        {
            "success": True,
            "message": "Booking request rejected successfully.",
            "data": {
                "booking_id": booking.id,
                "status": booking.status,
                "reject_reason": booking.reject_reason
            }
        },
        status=status.HTTP_200_OK
    )




@swagger_auto_schema(
    method="get",
    responses={200: PhotographerMyBookingSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_my_bookings(request):
    response = check_photographer_verification(request)
    if response:
        return response

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    # Show photographer's booking history and current work status
    bookings = Booking.objects.filter(
        photographer=photographer,
        status__in=[
            "photographer_accepted",
            "work_started",
            "in_progress",
            "completed",
            "photographer_rejected",
             "cancelled"
        ]
    ).select_related(
        "user"
    ).order_by(
        "-created_at"
    )

    serializer = PhotographerMyBookingSerializer(
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
@swagger_auto_schema(
    method="patch",
    request_body=UpdateWorkStatusSerializer
)
@api_view(["PATCH"])
@parser_classes([FormParser])
@permission_classes([IsAuthenticated])
def update_work_status(request, booking_id):

    # -----------------------------------
    # 1. CHECK PHOTOGRAPHER
    # -----------------------------------

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    # -----------------------------------
    # 2. GET PHOTOGRAPHER'S BOOKING
    # -----------------------------------

    try:
        booking = Booking.objects.get(
            id=booking_id,
            photographer=photographer
        )

    except Booking.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Booking not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------------
    # 3. VALIDATE REQUEST DATA
    # -----------------------------------

    serializer = UpdateWorkStatusSerializer(
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

    new_status = serializer.validated_data["status"]

    # -----------------------------------
    # 4. VALID STATUS TRANSITIONS
    # -----------------------------------

    allowed_transitions = {

        "photographer_accepted": [
            "work_started"
        ],

        "work_started": [
            "in_progress"
        ],

        "in_progress": [
            "completed"
        ]
    }

    current_status = booking.status

    # -----------------------------------
    # 5. CHECK CURRENT STATUS
    # -----------------------------------

    if current_status not in allowed_transitions:
        return Response(
            {
                "success": False,
                "message": (
                    f"Cannot update this booking. "
                    f"Current status is '{current_status}'."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 6. CHECK NEXT STATUS
    # -----------------------------------

    if new_status not in allowed_transitions[current_status]:
        return Response(
            {
                "success": False,
                "message": (
                    f"Invalid status transition from "
                    f"'{current_status}' to '{new_status}'."
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------------
    # 7. UPDATE BOOKING
    # -----------------------------------

    booking.status = new_status

    booking.save(
        update_fields=["status"]
    )

    # -----------------------------------
    # 8. SUCCESS RESPONSE
    # -----------------------------------

    return Response(
        {
            "success": True,
            "message": "Work status updated successfully.",
            "data": {
                "booking_id": booking.id,
                "previous_status": current_status,
                "current_status": booking.status
            }
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={
        200: PhotographerDashboardSerializer
    }
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_dashboard(request):

    # ---------------------------------------
    # CHECK PHOTOGRAPHER
    # ---------------------------------------

    if not hasattr(request.user, "photographer_profile"):

        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    # ---------------------------------------
    # GET PHOTOGRAPHER BOOKINGS
    # ---------------------------------------

    bookings = Booking.objects.filter(
        photographer=photographer
    )

    # ---------------------------------------
    # TOTAL BOOKINGS
    # ---------------------------------------

    total_bookings = bookings.count()

    # ---------------------------------------
    # COMPLETED BOOKINGS
    # ---------------------------------------

    completed_bookings = bookings.filter(
        status="completed"
    ).count()

    # ---------------------------------------
    # TOTAL EARNINGS
    # ---------------------------------------

    total_earnings = bookings.filter(
        status="completed"
    ).aggregate(
        total=Sum("photographer_amount")
    )["total"] or 0

    # ---------------------------------------
    # DASHBOARD DATA
    # ---------------------------------------

    data = {
        "total_bookings": total_bookings,
        "completed_bookings": completed_bookings,
        "total_earnings": total_earnings,
        "plan_mode": photographer.plan_mode
    }

    serializer = PhotographerDashboardSerializer(data)

    return Response(
        {
            "success": True,
            "message": "Dashboard data retrieved successfully.",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={200: PhotographerChargeSerializer(many=True)}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_service_charges(request):
    response = check_photographer_verification(request)
    if response:
        return response

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    charges = PhotographerCharge.objects.filter(
        photographer=photographer
    ).order_by("hours")

    serializer = PhotographerChargeSerializer(
        charges,
        many=True
    )

    return Response(
        {
            "success": True,
            "message": "Service charges retrieved successfully.",
            "data": serializer.data
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="patch",
    request_body=UpdatePhotographerChargeSerializer
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser])
def update_service_charge(request, charge_id):

    response = check_photographer_verification(request)
    if response:
        return response

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    try:
        charge = PhotographerCharge.objects.get(
            id=charge_id,
            photographer=photographer
        )
    except PhotographerCharge.DoesNotExist:
        return Response(
            {
                "success": False,
                "message": "Service charge not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = UpdatePhotographerChargeSerializer(
        charge,
        data=request.data,
        partial=True
    )

    if not serializer.is_valid():
        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer.save()

    return Response(
        {
            "success": True,
            "message": "Service charge updated successfully.",
            "data": {
                "id": charge.id,
                "hours": charge.hours,
                "amount": str(charge.amount)
            }
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="get",
    responses={200: PhotographerWalletSerializer}
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_wallet(request):

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    wallet, created = PhotographerWallet.objects.get_or_create(
        photographer=photographer
    )

    transactions = PhotographerWalletTransaction.objects.filter(
        photographer=photographer
    ).select_related(
        "booking",
        "photographer__user"
    ).order_by("-created_at")

    wallet_data = PhotographerWalletSerializer(wallet).data

    transaction_data = PhotographerWalletTransactionSerializer(
        transactions,
        many=True
    ).data

    return Response(
        {
            "success": True,
            "data": {
                "wallet": wallet_data,
                "transactions": transaction_data
            }
        },
        status=status.HTTP_200_OK
    )



@swagger_auto_schema(
    method="post"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def credit_photographer_wallet(request):

    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    wallet, created = PhotographerWallet.objects.get_or_create(
        photographer=photographer
    )

    bookings = Booking.objects.filter(
        photographer=photographer,
        status="completed"
    )

    credited_bookings = []

    for booking in bookings:

        # Already credited
        if PhotographerWalletTransaction.objects.filter(
            booking=booking
        ).exists():
            continue

        # Advance payment must be paid
        advance_payment = Payment.objects.filter(
            booking=booking,
            payment_type="advance",
            status="paid"
        ).first()

        if not advance_payment:
            continue

        # Balance payment must be paid
        balance_payment = Payment.objects.filter(
            booking=booking,
            payment_type="balance",
            status="paid"
        ).first()

        if not balance_payment:
            continue

        with transaction.atomic():

            wallet = PhotographerWallet.objects.select_for_update().get(
                id=wallet.id
            )

            # Check again to prevent duplicate credit
            if PhotographerWalletTransaction.objects.filter(
                booking=booking
            ).exists():
                continue

            amount = booking.photographer_amount

            wallet.balance += amount
            wallet.save(
                update_fields=["balance", "updated_at"]
            )

            PhotographerWalletTransaction.objects.create(
                photographer=photographer,
                wallet=wallet,
                booking=booking,
                amount=amount,
                transaction_type="booking",
                description=f"Earnings from completed booking #{booking.id}"
            )

            credited_bookings.append({
                "booking_id": booking.id,
                "amount": str(amount)
            })

    wallet.refresh_from_db()

    return Response(
        {
            "success": True,
            "message": "Photographer wallet credited successfully.",
            "data": {
                "wallet_id": wallet.id,
                "photographer_name": photographer.user.username,
                "balance": str(wallet.balance),
                "credited_bookings": credited_bookings
            }
        },
        status=status.HTTP_200_OK
    )





@swagger_auto_schema(
    method="get"
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def photographer_reschedule_requests(request):

    
    try:

        photographer = PhotographerProfile.objects.get(
            user=request.user
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Photographer profile not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    

    requests = RescheduleRequest.objects.filter(
        photographer=photographer
    ).select_related(
        "user",
        "photographer",
        "photographer__user",
        "booking"
    ).order_by(
        "-created_at"
    )

    

    data = []

    for reschedule in requests:

        data.append(
            {
                "reschedule_id": reschedule.id,

                "booking_id": reschedule.booking.id,

                "user_id": reschedule.user.id,

                "user_name": (
                    reschedule.user.username
                ),

                "photographer_id": (
                    reschedule.photographer.id
                ),

                "photographer_name": (
                    reschedule.photographer.user.username
                ),

                "old_date": reschedule.old_date,

                "old_time": reschedule.old_time,

                "old_session": (
                    reschedule.booking.session
                ),

                "new_date": reschedule.new_date,

                "new_time": reschedule.new_time,

                "new_session": reschedule.new_session,

                "description": reschedule.description,

                "status": reschedule.status,

                "created_at": reschedule.created_at,

                "responded_at": reschedule.responded_at
            }
        )

    

    return Response(
        {
            "success": True,

            "count": len(data),

            "data": data
        },
        status=status.HTTP_200_OK
    )






@swagger_auto_schema(
    method="post"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_reschedule(request, reschedule_id):

    

    try:

        photographer = PhotographerProfile.objects.get(
            user=request.user
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Photographer profile not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    # =================================================
    # 2. Start transaction
    # =================================================

    with transaction.atomic():

        # =================================================
        # 3. Get reschedule request
        # =================================================

        try:

            reschedule = (
                RescheduleRequest.objects
                .select_for_update()
                .select_related(
                    "booking",
                    "user",
                    "photographer"
                )
                .get(
                    id=reschedule_id,
                    photographer=photographer
                )
            )

        except RescheduleRequest.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Reschedule request not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND
            )

        

        if reschedule.status != "pending":

            return Response(
                {
                    "success": False,
                    "message": (
                        "This reschedule request has "
                        "already been responded to."
                    ),
                    "status": reschedule.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        

        try:

            booking = (
                Booking.objects
                .select_for_update()
                .get(
                    id=reschedule.booking.id
                )
            )

        except Booking.DoesNotExist:

            return Response(
                {
                    "success": False,
                    "message": "Booking not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        

        ALLOWED_STATUS = [
            "photographer_accepted",
            "confirmed",
        ]

        if booking.status not in ALLOWED_STATUS:

            return Response(
                {
                    "success": False,
                    "message": (
                        "This booking cannot be "
                        "rescheduled because of its "
                        "current status."
                    ),
                    "booking_status": booking.status
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        

        available = check_photographer_availability(
            photographer=photographer,

            selected_date=reschedule.new_date,

            session=reschedule.new_session,

            exclude_booking_id=booking.id
        )

        if not available:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Photographer is no longer "
                        "available for the requested "
                        "date and session."
                    ),

                    "new_date": reschedule.new_date,

                    "new_time": reschedule.new_time,

                    "new_session": (
                        reschedule.new_session
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        

        booking.date = reschedule.new_date

        booking.shoot_time = reschedule.new_time

        booking.session = reschedule.new_session

        booking.save(
            update_fields=[
                "date",
                "shoot_time",
                "session"
            ]
        )

        
        reschedule.status = "accepted"

        reschedule.responded_at = timezone.now()

        reschedule.save(
            update_fields=[
                "status",
                "responded_at"
            ]
        )

    
    return Response(
        {
            "success": True,

            "message": (
                "Reschedule request accepted "
                "successfully."
            ),

            "data": {

                "reschedule_id": reschedule.id,

                "booking_id": booking.id,

                "status": reschedule.status,

                "date": booking.date,

                "shoot_time": booking.shoot_time,

                "session": booking.session,

                "responded_at": (
                    reschedule.responded_at
                )
            }
        },
        status=status.HTTP_200_OK
    )





@swagger_auto_schema(
    method="post"
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_reschedule(request, reschedule_id):

    

    try:

        photographer = PhotographerProfile.objects.get(
            user=request.user
        )

    except PhotographerProfile.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Photographer profile not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    

    try:

        reschedule = RescheduleRequest.objects.get(
            id=reschedule_id,
            photographer=photographer
        )

    except RescheduleRequest.DoesNotExist:

        return Response(
            {
                "success": False,
                "message": "Reschedule request not found."
            },
            status=status.HTTP_404_NOT_FOUND
        )

    

    if reschedule.status != "pending":

        return Response(
            {
                "success": False,
                "message": (
                    "This reschedule request has "
                    "already been responded to."
                ),
                "status": reschedule.status
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    

    reschedule.status = "rejected"

    reschedule.responded_at = timezone.now()

    reschedule.save(
        update_fields=[
            "status",
            "responded_at"
        ]
    )

    

    return Response(
        {
            "success": True,

            "message": (
                "Reschedule request rejected "
                "successfully."
            ),

            "data": {

                "reschedule_id": reschedule.id,

                "booking_id": reschedule.booking.id,

                "status": reschedule.status,

                "responded_at": (
                    reschedule.responded_at
                )
            }
        },
        status=status.HTTP_200_OK
    )


class PhotographerGoogleLoginView(APIView):

    @swagger_auto_schema(
        request_body=PhotographerGoogleLoginSerializer
    )
    def post(self, request):
        serializer = PhotographerGoogleLoginSerializer(
            data=request.data
        )

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

        if not user:
            return Response({
                "success": False,
                "message": (
                    "Photographer account not found. "
                    "Please register as a photographer first."
                )
            }, status=status.HTTP_404_NOT_FOUND)

        # Block normal-user accounts and conflicting roles
        if UserProfile.objects.filter(user=user).exists():
            return Response({
                "success": False,
                "message": (
                    "This email belongs to a normal user. "
                    "Please use User Login."
                )
            }, status=status.HTTP_403_FORBIDDEN)

        photographer = PhotographerProfile.objects.filter(
            user=user
        ).first()

        if not photographer:
            return Response({
                "success": False,
                "message": "Photographer profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Photographer Google login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "photographer": {
                "id": photographer.id,
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "verification_status": photographer.verification_status,
                "is_verified": photographer.is_verified
            }
        }, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    request_body=PhotographerForgotPasswordSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
def photographer_forgot_password(request):

    serializer = PhotographerForgotPasswordSerializer(
        data=request.data
    )

    if serializer.is_valid():

        email = serializer.validated_data["email"].strip().lower()

        # Check whether this email belongs to a photographer
        user = User.objects.filter(email__iexact=email).first()

        if not user or not PhotographerProfile.objects.filter(user=user).exists():
            return Response(
                {"error": "No photographer account found with this email."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate OTP
        otp = str(random.randint(100000, 999999))

        # Remove old OTP
        PhotographerPasswordResetOTP.objects.filter(
            email__iexact=user.email
        ).delete()

        # Save new OTP
        PhotographerPasswordResetOTP.objects.create(
            email=user.email,
            otp=otp,
            created_at=timezone.now()
        )

        # Send OTP
        try:
            send_mail(
                subject="SnapsHire - Photographer Password Reset",
                message=f"""
Hello,

We received a request to reset your SnapsHire photographer account password.

Your verification code is: {otp}

This code is valid for 5 minutes. Please do not share this code with anyone.

If you did not request a password reset, you may safely disregard this email.

Regards,
SnapsHire Team
Photography Booking Platform
""",
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            PhotographerPasswordResetOTP.objects.filter(
                email__iexact=user.email
            ).delete()

            return Response(
                {"error": "Unable to send OTP. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(
            {"message": "OTP sent successfully. Please check your email."},
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="post",
    request_body=PhotographerResetPasswordSerializer
)
@api_view(["POST"])
@parser_classes([FormParser])
def photographer_reset_password(request):

    serializer = PhotographerResetPasswordSerializer(
        data=request.data
    )

    if serializer.is_valid():

        email = serializer.validated_data["email"].strip().lower()
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        # Find the photographer account
        user = User.objects.filter(email__iexact=email).first()

        if not user or not PhotographerProfile.objects.filter(user=user).exists():
            return Response(
                {"error": "Photographer account not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            otp_record = PhotographerPasswordResetOTP.objects.get(
                email__iexact=user.email
            )
        except PhotographerPasswordResetOTP.DoesNotExist:
            return Response(
                {"error": "OTP not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check OTP expiry
        if timezone.now() > otp_record.created_at + timedelta(minutes=5):
            otp_record.delete()

            return Response(
                {"error": "OTP has expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check OTP
        if otp_record.otp != otp:
            return Response(
                {"error": "Invalid OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update password securely
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Delete OTP after successful reset
        otp_record.delete()

        return Response(
            {"message": "Photographer password reset successful."},
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )



import razorpay

from django.conf import settings
from django.db import transaction

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

from .models import VerificationPayment
from .serializers import VerifyVerificationPaymentSerializer


@swagger_auto_schema(
    method="post",
    request_body=VerifyVerificationPaymentSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser, JSONParser])
def verify_verification_payment(request):
    serializer = VerifyVerificationPaymentSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    order_id = serializer.validated_data["razorpay_order_id"]
    payment_id = serializer.validated_data["razorpay_payment_id"]
    signature = serializer.validated_data["razorpay_signature"]

    try:
        profile = request.user.photographer_profile
    except AttributeError:
        return Response(
            {"error": "Photographer profile not found."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        payment_record = VerificationPayment.objects.get(
            razorpay_order_id=order_id,
            photographer=profile,
        )
    except VerificationPayment.DoesNotExist:
        return Response(
            {"error": "Payment order not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if payment_record.status == "paid":
        return Response(
            {"message": "This payment has already been verified."},
            status=status.HTTP_200_OK,
        )

    if payment_record.status != "pending":
        return Response(
            {"error": "This payment is not pending."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )

    # Verify the Razorpay checkout signature.
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return Response(
            {"error": "Invalid payment signature."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        return Response(
            {"error": "Unable to verify payment. Please try again."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # Confirm payment details directly with Razorpay.
    try:
        razorpay_payment = client.payment.fetch(payment_id)
    except Exception:
        return Response(
            {"error": "Unable to retrieve payment status."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    expected_amount = int(payment_record.amount * 100)

    if (
        razorpay_payment.get("order_id") != order_id
        or razorpay_payment.get("amount") != expected_amount
        or razorpay_payment.get("currency") != payment_record.currency
    ):
        return Response(
            {"error": "Payment details do not match the order."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if razorpay_payment.get("status") != "captured":
        return Response(
            {
                "message": "Payment has not been captured yet.",
                "payment_status": razorpay_payment.get("status"),
            },
            status=status.HTTP_409_CONFLICT,
        )

    # Lock the payment record to prevent concurrent activation.
    with transaction.atomic():
        payment_record = VerificationPayment.objects.select_for_update().get(
            pk=payment_record.pk
        )

        if payment_record.status == "paid":
            return Response(
                {"message": "This payment has already been verified."},
                status=status.HTTP_200_OK,
            )

        if payment_record.status != "pending":
            return Response(
                {"error": "This payment is not pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.plan_mode = payment_record.plan_mode
        profile.save(update_fields=["plan_mode"])

        payment_record.razorpay_payment_id = payment_id
        payment_record.status = "paid"
        payment_record.save(
            update_fields=["razorpay_payment_id", "status"]
        )

    return Response(
        {
            "message": "Payment verified and plan activated successfully.",
            "plan_mode": profile.plan_mode,
            "amount": str(payment_record.amount),
            "payment_status": payment_record.status,
        },
        status=status.HTTP_200_OK,
    )

@swagger_auto_schema(
    method="post",
    request_body=CreateVerificationOrderSerializer,
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([FormParser, JSONParser])
def create_verification_order(request):

    # 1. Get photographer profile
    try:
        profile = request.user.photographer_profile
    except AttributeError:
        return Response(
            {"error": "Photographer profile not found."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # 2. Validate selected plan
    serializer = CreateVerificationOrderSerializer(
        data=request.data
    )

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    plan_mode = serializer.validated_data["plan_mode"]

    # 3. Prevent selecting the current plan again
    if profile.plan_mode == plan_mode:
        return Response(
            {"error": f"You are already using the {plan_mode} plan."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4. Get admin-configured price
    try:
        plan = VerificationPlan.objects.get(
            plan_name=plan_mode,
            is_active=True,
        )
    except VerificationPlan.DoesNotExist:
        return Response(
            {"error": "Selected plan is unavailable."},
            status=status.HTTP_404_NOT_FOUND,
        )

    amount = plan.verification_charge

    # 5. Convert rupees to paise
    amount_in_paise = int(amount * Decimal("100"))

    if (
        amount <= 0
        or amount * Decimal("100") != amount_in_paise
    ):
        return Response(
            {"error": "Invalid verification charge."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 6. Create Razorpay order
    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
        )
    )

    try:
        order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"verify_{profile.pk}_{plan_mode}",
            "notes": {
                "photographer_id": str(profile.pk),
                "plan_mode": plan_mode,
            },
        })
    except Exception:
        return Response(
            {"error": "Unable to create Razorpay order."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 7. Save payment record
    try:
        with transaction.atomic():
            payment = VerificationPayment.objects.create(
                photographer=profile,
                plan_mode=plan_mode,
                amount=amount,
                razorpay_order_id=order["id"],
                status="pending",
            )
    except Exception:
        # The Razorpay order exists, but the local record failed.
        # Do not activate the plan. Log and reconcile this order.
        return Response(
            {
                "error": "Order was created, but saving the payment record failed.",
                "razorpay_order_id": order["id"],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 8. Return payment details to frontend
    return Response(
        {
            "message": "Payment order created successfully.",
            "payment_id": payment.id,
            "plan_mode": payment.plan_mode,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "payment_status": payment.status,
            "razorpay_order_id": order["id"],
           
        },
        status=status.HTTP_201_CREATED,
    )


@swagger_auto_schema(
    method="get",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verification_transactions(request):

    # Check whether the user is a photographer
    if not hasattr(request.user, "photographer_profile"):
        return Response(
            {
                "success": False,
                "message": "You are not a photographer."
            },
            status=status.HTTP_403_FORBIDDEN
        )

    photographer = request.user.photographer_profile

    # Get only this photographer's verification payments
    payments = VerificationPayment.objects.filter(
        photographer=photographer
    ).order_by("-created_at")

    transactions = []

    for payment in payments:
        transactions.append({
            "transaction_id": payment.id,
            "transaction_type": "verification_payment",
            "plan_mode": payment.plan_mode,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": (
                payment.razorpay_payment_id or None
            ),
            "status": payment.status,
            "created_at": payment.created_at,
        })

    return Response(
        {
            "success": True,
            "message": "Verification transactions retrieved successfully.",
            "count": len(transactions),
            "transactions": transactions
        },
        status=status.HTTP_200_OK
    )





