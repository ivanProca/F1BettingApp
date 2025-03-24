# betting/views.py

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages

from .models import Race, Bet, Season, RaceResult, Driver
from .forms import BetForm, UserRegistrationForm

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def home(request):
    # Show upcoming races and leaderboard
    current_season = Season.objects.filter(is_active=True).first()
    
    # Upcoming races
    upcoming_races = Race.objects.filter(
        season=current_season,
        race_date__gt=timezone.now()
    ).order_by('race_date')[:5]
    
    # Completed races
    completed_races = Race.objects.filter(
        season=current_season,
        is_completed=True
    ).order_by('race_date')
    
    # Simple leaderboard based on total points
    leaderboard = Bet.objects.filter(
        race__season=current_season
    ).values('user__username').annotate(
        total_points=Sum('points')
    ).order_by('-total_points')[:10]
    
    # Prepare data for classification line graph
    classification_data = prepare_classification_graph_data(current_season)
    
    # Convert classification data to JSON for template
    classification_json = json.dumps({
        username: {
            'username': data['username'],
            'cumulative_points': data['cumulative_points']
        } for username, data in classification_data.items()
    })
    
    return render(request, 'betting/home.html', {
        'upcoming_races': upcoming_races,
        'completed_races': completed_races,
        'leaderboard': leaderboard,
        'classification_json': classification_json,
    })

def prepare_classification_graph_data(season):
    """
    Prepare data for line graph showing classification evolution
    """
    # Get all completed races for the season
    completed_races = Race.objects.filter(
        season=season,
        is_completed=True
    ).order_by('race_date')
    
    # Prepare data structure for graph
    classification_evolution = {}
    
    # Iterate through races to build cumulative points
    for race in completed_races:
        # Get bets for this race
        race_bets = Bet.objects.filter(race=race)
        
        for bet in race_bets:
            username = bet.user.username
            
            # Initialize user data if not exists
            if username not in classification_evolution:
                classification_evolution[username] = {
                    'username': username,
                    'points_per_race': [0] * len(completed_races),
                    'cumulative_points': [0] * len(completed_races)
                }
            
            # Find the race index
            race_index = list(completed_races).index(race)
            
            # Add points for this race
            classification_evolution[username]['points_per_race'][race_index] = bet.points
    
    # Calculate cumulative points
    for username, data in classification_evolution.items():
        cumulative = 0
        cumulative_points = []
        
        for points in data['points_per_race']:
            cumulative += points
            cumulative_points.append(cumulative)
        
        data['cumulative_points'] = cumulative_points
    
    return classification_evolution

@login_required
def race_detail(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    user_bet = Bet.objects.filter(user=request.user, race=race).first()
    
    # Check if betting is closed
    betting_closed = timezone.now() >= race.practice_start
    
    # If race is completed, show results
    if race.is_completed:
        race_result = race.result
        all_bets = Bet.objects.filter(race=race).order_by('-points')
        return render(request, 'betting/race_results.html', {
            'race': race,
            'user_bet': user_bet,
            'race_result': race_result,
            'all_bets': all_bets,
        })
    
    # If betting is still open, show form
    if not betting_closed:
        if request.method == 'POST':
            if user_bet:
                form = BetForm(request.POST, instance=user_bet)
            else:
                form = BetForm(request.POST)
                
            if form.is_valid():
                bet = form.save(commit=False)
                bet.user = request.user
                bet.race = race
                bet.save()
                messages.success(request, "Your bet has been saved!")
                return redirect('race_detail', race_id=race.id)
        else:
            form = BetForm(instance=user_bet)
            
        return render(request, 'betting/place_bet.html', {
            'race': race,
            'form': form,
            'user_bet': user_bet,
        })
    
    # If betting is closed but race not completed
    return render(request, 'betting/betting_closed.html', {
        'race': race,
        'user_bet': user_bet,
    })

@login_required
def season_standings(request, season_id=None):
    if season_id:
        season = get_object_or_404(Season, pk=season_id)
    else:
        season = Season.objects.filter(is_active=True).first()
    
    # Calculate standings
    standings = Bet.objects.filter(
        race__season=season
    ).values('user__username').annotate(
        total_points=Sum('points')
    ).order_by('-total_points')
    
    # Get list of all seasons for the dropdown
    all_seasons = Season.objects.all().order_by('-year')
    
    return render(request, 'betting/standings.html', {
        'season': season,
        'standings': standings,
        'all_seasons': all_seasons,
    })

# Admin view to enter race results
@login_required
def enter_race_result(request, race_id):
    race = get_object_or_404(Race, pk=race_id)
    
    # Only allow superusers to enter results
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to enter race results.")
        return redirect('home')
    
    if request.method == 'POST':
        first_place_quali_id = request.POST.get('first_place_quali')
        second_place_quali_id = request.POST.get('second_place_quali')
        third_place_quali_id = request.POST.get('third_place_quali')
        first_place_race_id = request.POST.get('first_place_race')
        second_place_race_id = request.POST.get('second_place_race')
        third_place_race_id = request.POST.get('third_place_race')
        dnf_count = request.POST.get('dnf_count')
        
        # Create or update race result
        result, created = RaceResult.objects.update_or_create(
            race=race,
            defaults={
                'first_place_quali_id': first_place_quali_id,
                'second_place_quali_id': second_place_quali_id,
                'third_place_quali_id': third_place_quali_id,
                'first_place_race_id': first_place_race_id,
                'second_place_race_id': second_place_race_id,
                'third_place_race_id': third_place_race_id,
                'dnf_count': dnf_count,
            }
        )
        
        # Mark race as completed
        race.is_completed = True
        race.dnf_count = dnf_count
        race.save()
        
        # Calculate points for all bets
        calculate_points(race)
        
        messages.success(request, "Race results saved and points calculated.")
        return redirect('race_detail', race_id=race.id)
    
    # Show form to enter results
    active_drivers = Driver.objects.filter(is_active=True)
    
    return render(request, 'betting/enter_results.html', {
        'race': race,
        'drivers': active_drivers,
    })

def calculate_points(race):
    """Calculate points for all bets for a specific race"""
    race_result = race.result
    bets = Bet.objects.filter(race=race)
    
    for bet in bets:
        points = 0
        
        # Points for correct podium positions
        if bet.first_place == race_result.first_place:
            points += 10
        if bet.second_place == race_result.second_place:
            points += 5
        if bet.third_place == race_result.third_place:
            points += 3
            
        # Partial points for correct driver but wrong position
        drivers = [race_result.first_place, race_result.second_place, race_result.third_place]
        if bet.first_place in drivers and bet.first_place != race_result.first_place:
            points += 2
        if bet.second_place in drivers and bet.second_place != race_result.second_place:
            points += 1
        if bet.third_place in drivers and bet.third_place != race_result.third_place:
            points += 1
            
        # Points for correct DNF count
        if bet.dnf_prediction == race_result.dnf_count:
            points += 5
        # Partial points for close DNF prediction
        elif abs(bet.dnf_prediction - race_result.dnf_count) == 1:
            points += 2
            
        # Save points
        bet.points = points
        bet.save()

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Save the form and get the user object
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You are now logged in.')
            
            # Auto-login the user after registration
            login(request, user)
            
            return redirect('home')  # Redirect to home page instead of login page
    else:
        form = UserRegistrationForm()
    return render(request, 'betting/register.html', {'form': form})

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
    
    return render(request, 'home.html')

def rules_page(request):
    return render(request, 'betting/rules.html')