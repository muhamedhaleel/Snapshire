import os

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.shortcuts import redirect, render

from .models import PhotographerProfile, PortfolioFile, PortfolioLink


MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_PORTFOLIO_LINKS = 5
MAX_PORTFOLIO_FILES = 3
MAX_PORTFOLIO_FILE_SIZE = 10 * 1024 * 1024


def _validate_profile_image(image_file):
    errors = []
    extension = os.path.splitext(image_file.name)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        errors.append('Profile image must be JPG, PNG, or WEBP.')
    if image_file.size > MAX_PROFILE_IMAGE_SIZE:
        errors.append('Profile image must be 5 MB or smaller.')
    return errors


def _normalize_portfolio_url(url):
    url = url.strip()
    if not url:
        return None
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    validator = URLValidator()
    validator(url)
    return url


def _parse_portfolio_links(raw_links):
    errors = []
    cleaned_links = []
    seen = set()

    for index, raw_url in enumerate(raw_links, start=1):
        url = raw_url.strip()
        if not url:
            continue

        if len(cleaned_links) >= MAX_PORTFOLIO_LINKS:
            errors.append(f'You can add up to {MAX_PORTFOLIO_LINKS} portfolio links.')
            break

        try:
            normalized_url = _normalize_portfolio_url(url)
        except ValidationError:
            errors.append(f'Portfolio link {index} must be a valid URL (http or https).')
            continue

        if normalized_url in seen:
            continue

        seen.add(normalized_url)
        cleaned_links.append(normalized_url)

    return cleaned_links, errors


def _validate_portfolio_pdf(pdf_file):
    errors = []
    extension = os.path.splitext(pdf_file.name)[1].lower()
    if extension != '.pdf':
        errors.append(f'"{pdf_file.name}" must be a PDF file.')
    if pdf_file.size > MAX_PORTFOLIO_FILE_SIZE:
        errors.append(f'"{pdf_file.name}" must be 10 MB or smaller.')
    return errors


def _parse_portfolio_files(profile, remove_file_ids, uploaded_files):
    errors = []
    valid_remove_ids = []

    for file_id in remove_file_ids:
        if str(file_id).isdigit():
            valid_remove_ids.append(int(file_id))

    files_to_remove = profile.portfolio_files.filter(id__in=valid_remove_ids)
    remaining_count = profile.portfolio_files.exclude(id__in=valid_remove_ids).count()

    if remaining_count + len(uploaded_files) > MAX_PORTFOLIO_FILES:
        errors.append(f'You can upload up to {MAX_PORTFOLIO_FILES} portfolio PDF files.')

    cleaned_files = []
    for pdf_file in uploaded_files:
        file_errors = _validate_portfolio_pdf(pdf_file)
        if file_errors:
            errors.extend(file_errors)
        else:
            cleaned_files.append(pdf_file)

    return files_to_remove, cleaned_files, errors


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
        remove_profile_image = request.POST.get('remove_profile_image') == '1'
        portfolio_links = request.POST.getlist('portfolio_links')
        remove_portfolio_files = request.POST.getlist('remove_portfolio_files')
        portfolio_pdfs = request.FILES.getlist('portfolio_pdfs')

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

        cleaned_portfolio_links, portfolio_errors = _parse_portfolio_links(portfolio_links)
        errors.extend(portfolio_errors)

        files_to_remove, cleaned_portfolio_files, portfolio_file_errors = _parse_portfolio_files(
            profile,
            remove_portfolio_files,
            portfolio_pdfs,
        )
        errors.extend(portfolio_file_errors)

        profile_image = request.FILES.get('profile_image')
        if profile_image:
            errors.extend(_validate_profile_image(profile_image))

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

            if remove_profile_image and profile.profile_image:
                profile.profile_image.delete(save=False)
                profile.profile_image = None
            elif profile_image:
                if profile.profile_image:
                    profile.profile_image.delete(save=False)
                profile.profile_image = profile_image

            profile.save()

            profile.portfolio_links.all().delete()
            for url in cleaned_portfolio_links:
                PortfolioLink.objects.create(profile=profile, url=url)

            for portfolio_file in files_to_remove:
                portfolio_file.delete()

            for pdf_file in cleaned_portfolio_files:
                PortfolioFile.objects.create(profile=profile, file=pdf_file, original_name=pdf_file.name)

            messages.success(request, 'Profile updated successfully.')

        return redirect('photographer_edit_profile')

    portfolio_links = list(profile.portfolio_links.all())
    portfolio_files = list(profile.portfolio_files.all())
    verification_status, completed_steps, total_steps = _profile_verification_status(profile)

    return render(request, 'photographer-editprofile.html', {
        'profile': profile,
        'portfolio_links': portfolio_links,
        'portfolio_files': portfolio_files,
        'max_portfolio_links': MAX_PORTFOLIO_LINKS,
        'max_portfolio_files': MAX_PORTFOLIO_FILES,
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
                inactive_user = User.objects.filter(username=username).first()
                if inactive_user and not inactive_user.is_active:
                    errors.append('This account has been blocked. Contact support.')
                else:
                    errors.append('Invalid username or password.')
            elif not PhotographerProfile.objects.filter(user=user).exists():
                errors.append('This account is not registered as a photographer.')
            elif not user.is_active:
                errors.append('This account has been blocked. Contact support.')

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
