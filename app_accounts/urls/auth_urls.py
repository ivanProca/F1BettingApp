from django.urls import path
from app_accounts.views.auth_views import login_view, register_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
]