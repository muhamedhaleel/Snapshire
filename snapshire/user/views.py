from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from .models import UserProfile


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = UserProfile.objects.filter(user=request.user).first()
    return render(request, 'user-home.html', {'profile': profile})


def user_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

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

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')

    return render(request, 'user-login.html', {'username': username})


def signup(request):
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
            UserProfile.objects.create(user=user)
            messages.success(request, 'Account created successfully. You can log in now.')
            return redirect('login')

    return render(request, 'user-signup.html')
