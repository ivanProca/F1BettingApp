# betting/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', views.home, name='home'),
    path('race/<int:race_id>/', views.race_detail, name='race_detail'),
    path('standings/', views.season_standings, name='current_standings'),
    path('standings/<int:season_id>/', views.season_standings, name='season_standings'),
    path('race/<int:race_id>/enter-results/', views.enter_race_result, name='enter_race_result'),
    path('register/', views.register_view, name='register'),
    path('rules/', views.rules_page, name='rules_page'),
    path('races/', views.all_races_view, name='all_races'),

    #New profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/email/', views.update_email, name='update_email'),
    path('profile/password/', views.change_password, name='change_password'),

    # Password reset URLs (built-in Django views)
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='betting/password_reset.html',
             email_template_name='betting/password_reset_email.html',
             subject_template_name='betting/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='betting/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='betting/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='betting/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]