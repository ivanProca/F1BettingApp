# betting/urls.py
from django.urls import path
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
]

# Add these to main urls.py
# from django.urls import path, include
# 
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('betting.urls')),
#     path('accounts/', include('django.contrib.auth.urls')),
# ]