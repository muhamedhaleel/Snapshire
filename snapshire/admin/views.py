from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from photographer.models import PhotographerProfile
from user.models import UserProfile


def _require_superuser(request):
    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser account required.')
        logout(request)
        return redirect('admin_login')

    return None


def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_home')
        logout(request)
        messages.info(request, 'Signed out of your previous account. Log in with your superuser credentials.')

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

        if not errors:
            user = authenticate(request, username=username, password=password)
            if user is None:
                errors.append('Invalid username or password.')
            elif not user.is_superuser:
                errors.append(
                    'This account is not a superuser id '
                    
                )

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('admin_home')

    return render(request, 'admin-login.html', {'username': username})


def admin_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')


def admin_home(request):
    redirect_response = _require_superuser(request)
    if redirect_response:
        return redirect_response

    user_count = UserProfile.objects.count()
    photographer_count = PhotographerProfile.objects.count()
    total_accounts = User.objects.filter(is_superuser=False).count()
    blocked_users = UserProfile.objects.filter(user__is_active=False).count()
    blocked_photographers = PhotographerProfile.objects.filter(user__is_active=False).count()

    return render(request, 'admin-home.html', {
        'user_count': user_count,
        'photographer_count': photographer_count,
        'total_accounts': total_accounts,
        'blocked_users': blocked_users,
        'blocked_photographers': blocked_photographers,
    })


def _toggle_account_block(request, user_id, profile_check, redirect_name, account_label):
    redirect_response = _require_superuser(request)
    if redirect_response:
        return redirect_response

    if request.method != 'POST':
        return redirect(redirect_name)

    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        messages.error(request, f'{account_label} not found.')
        return redirect(redirect_name)

    if target.is_superuser:
        messages.error(request, 'Cannot block a superuser account.')
        return redirect(redirect_name)

    if not profile_check(target):
        messages.error(request, f'This account is not a registered {account_label.lower()}.')
        return redirect(redirect_name)

    target.is_active = not target.is_active
    target.save()

    if target.is_active:
        messages.success(request, f'{target.username} has been unblocked.')
    else:
        messages.success(request, f'{target.username} has been blocked.')

    return redirect(redirect_name)


def admin_toggle_user_block(request, user_id):
    return _toggle_account_block(
        request,
        user_id,
        lambda user: UserProfile.objects.filter(user=user).exists(),
        'admin_user_list',
        'User',
    )


def admin_toggle_photographer_block(request, user_id):
    return _toggle_account_block(
        request,
        user_id,
        lambda user: PhotographerProfile.objects.filter(user=user).exists(),
        'admin_photographer_list',
        'Photographer',
    )


def admin_user_list(request):
    redirect_response = _require_superuser(request)
    if redirect_response:
        return redirect_response
    search = request.GET.get('search')

    users = UserProfile.objects.select_related('user')
    if search:
        users= users.filter(
            user__username__icontains=search
        )
        
    users = users.order_by('-created_at')
    paginator = Paginator(users, 3)

    page_number = request.GET.get('page')
    print("Current Page:", page_number)

    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin-userlist.html', {
        'users': page_obj,
        'page_obj': page_obj,
        'search': search,
    })


def admin_photographer_list(request):
    redirect_response = _require_superuser(request)
    if redirect_response:
        return redirect_response
    search = request.GET.get('search', '')


    photographers = PhotographerProfile.objects.select_related('user')
    
    if search:
        photographers = photographers.filter(
            user__username__icontains=search
        )

    photographers = photographers.order_by('-created_at')
    # Pagination (5 records per page)
    paginator = Paginator(photographers, 3)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(request, 'admin-photographerlist.html', {
        'photographers': page_obj,
        'page_obj': page_obj,
        'search': search,
    })
    
