from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .models import PhotographerProfile


def _require_photographer(request):
    if not request.user.is_authenticated:
        return None, redirect('photographer_login')

    if not PhotographerProfile.objects.filter(user=request.user).exists():
        messages.error(request, 'This account is not registered as a photographer.')
        logout(request)
        return None, redirect('photographer_login')

    return request.user.photographer_profile, None


def _profile_verification_status(profile):
    required_fields = [profile.phone, profile.bio, profile.specialty, profile.location]
    completed = sum(1 for value in required_fields if value.strip())
    if completed == len(required_fields):
        return 'ready', completed, len(required_fields)
    return 'pending', completed, len(required_fields)


def photographer_verification(request):
    profile, redirect_response = _require_photographer(request)
    if redirect_response:
        return redirect_response

    verification_status, completed_steps, total_steps = _profile_verification_status(profile)
    profile_complete = profile.is_profile_complete

    if request.method == 'POST':
        plan = request.POST.get('plan', '').strip()

        if not profile_complete:
            messages.error(request, 'Complete all profile fields before choosing a plan.')
            return redirect('photographer_verification')

        if plan == PhotographerProfile.PLAN_FREE:
            profile.plan_mode = PhotographerProfile.PLAN_FREE
            profile.save()
            messages.success(request, 'Your profile is now on the Free plan.')
            return redirect('photographer_home')

        if plan in (PhotographerProfile.PLAN_GOLD, PhotographerProfile.PLAN_PLATINUM):
            plan_name = 'Gold' if plan == PhotographerProfile.PLAN_GOLD else 'Platinum'
            messages.info(
                request,
                f'{plan_name} plan is in demo mode. Payment is not processed yet — coming soon.',
            )
            return redirect('photographer_verification')

        messages.error(request, 'Please select a valid plan.')

    return render(request, 'photographer_verfication.html', {
        'profile': profile,
        'verification_status': verification_status,
        'verification_completed': completed_steps,
        'verification_total': total_steps,
        'profile_complete': profile_complete,
    })


def photographer_home(request):
    profile, redirect_response = _require_photographer(request)
    if redirect_response:
        return redirect_response

    verification_status, completed_steps, total_steps = _profile_verification_status(profile)

    return render(request, 'photographer-home.html', {
        'profile': profile,
        'verification_status': verification_status,
        'verification_completed': completed_steps,
        'verification_total': total_steps,
    })


def photographer_edit_profile(request):
    profile, redirect_response = _require_photographer(request)
    if redirect_response:
        return redirect_response

    if request.method == 'POST':
        user = request.user
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        specialty = request.POST.get('specialty', '').strip()
        location = request.POST.get('location', '').strip()

        errors = []

        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif User.objects.filter(username=username).exclude(pk=user.pk).exists():
            errors.append('This username is already taken.')

        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            errors.append('This email is already registered.')

        if phone and len(phone) < 10:
            errors.append('Phone number must be at least 10 digits.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user.username = username
            user.email = email
            user.save()
            profile.phone = phone
            profile.bio = bio
            profile.specialty = specialty
            profile.location = location
            profile.save()
            messages.success(request, 'Profile updated successfully.')

        return redirect('photographer_edit_profile')

    verification_status, completed_steps, total_steps = _profile_verification_status(profile)

    return render(request, 'photographer-editprofile.html', {
        'profile': profile,
        'verification_status': verification_status,
        'verification_completed': completed_steps,
        'verification_total': total_steps,
    })


def photographer_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('photographer_login')


def photographer_login(request):
    if request.user.is_authenticated and PhotographerProfile.objects.filter(user=request.user).exists():
        return redirect('photographer_home')

    username = ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        errors = []

        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if not errors:
            user = authenticate(request, username=username, password=password)
            if user is None:
                errors.append('Invalid username or password.')
            elif not PhotographerProfile.objects.filter(user=user).exists():
                errors.append('This account is not registered as a photographer.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('photographer_home')

    return render(request, 'photographer-login.html', {'username': username})


def photographer_signup(request):
    if request.user.is_authenticated and PhotographerProfile.objects.filter(user=request.user).exists():
        return redirect('photographer_home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []

        if not username:
            errors.append('Username is required.')
        elif len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        elif User.objects.filter(username=username).exists():
            errors.append('This username is already taken.')

        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('This email is already registered.')

        if not password:
            errors.append('Password is required.')
        elif len(password) < 8:
            errors.append('Password must be at least 8 characters.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            PhotographerProfile.objects.create(user=user)
            messages.success(request, 'Photographer account created successfully. You can log in now.')
            return redirect('photographer_login')

    return render(request, 'photographer-signup.html')
