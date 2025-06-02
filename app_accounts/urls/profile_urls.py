from django.urls import path
from app_accounts.views.profile_views import profile_view, update_profile, update_email, change_password

urlpatterns = [
    path('', profile_view, name='profile'),
    path('update/', update_profile, name='update_profile'),
    path('email/', update_email, name='update_email'),
    path('password/', change_password, name='change_password'),
]