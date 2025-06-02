from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Password reset URLs (built-in Django views)
    path('',
        auth_views.PasswordResetView.as_view(
            template_name='app_accounts/password_reset.html',
            email_template_name='app_accounts/password_reset_email.html',
            subject_template_name='app_accounts/password_reset_subject.txt'
        ),
        name='password_reset'),
    path('done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='app_accounts/password_reset_done.html'
        ),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='app_accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'),
    path('reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='app_accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'),
]