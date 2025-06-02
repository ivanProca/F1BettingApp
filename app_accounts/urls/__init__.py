from django.urls import path, include

urlpatterns = [
    path('', include('app_accounts.urls.auth_urls')),
    path('profile/', include('app_accounts.urls.profile_urls')),
    path('password_reset/', include('app_accounts.urls.password_reset_urls')),
]