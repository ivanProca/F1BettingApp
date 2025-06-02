from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User

@login_required
def profile_view(request):
    """Display the user profile page"""
    return render(request, 'app_accounts/profile.html')

@login_required
def update_profile(request):
    """Update the user's username"""
    if request.method == 'POST':
        username = request.POST.get('username')
        
        # Check if username already exists and it's not the current user
        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            messages.error(request, 'Username already exists. Please choose another one.')
            return redirect('profile')
        
        # Update username
        user = request.user
        user.username = username
        user.save()
        
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('profile')
    
    return redirect('profile')

@login_required
def update_email(request):
    """Update the user's email address"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Check if email already exists and it's not the current user
        if email and User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, 'Email already exists. Please use another one.')
            return redirect('profile')
        
        # Update email
        user = request.user
        user.email = email
        user.save()
        
        messages.success(request, 'Your email has been updated successfully!')
        return redirect('profile')
    
    return redirect('profile')

@login_required
def change_password(request):
    """Change the user's password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Check if the current password is correct
        if not request.user.check_password(current_password):
            messages.error(request, 'Your current password is incorrect.')
            return redirect('profile')
        
        # Check if the new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'The new passwords do not match.')
            return redirect('profile')
        
        # Check if the new password meets requirements
        if len(new_password1) < 8:
            messages.error(request, 'Your new password must be at least 8 characters long.')
            return redirect('profile')
        
        # Update password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Your password has been changed successfully!')
        return redirect('profile')
    
    return redirect('profile')