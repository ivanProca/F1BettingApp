from django.shortcuts import render, redirect
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Form validation
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('app_accounts/register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('app_accounts/register')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('app_accounts/register')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('app_accounts/register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # Log in the user
        login(request, user)

        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('home') # Redirect to home page
    
    return render(request, 'app_accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Change 'home' to your home page URL name
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'app_accounts/login.html')