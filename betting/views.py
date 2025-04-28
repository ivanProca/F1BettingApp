# betting/views.py

import json

from django.conf import settings

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
    ).order_by('race_date')[:3]
    
    # Completed races
    completed_races = Race.objects.filter(
        season=current_season,
        is_completed=True
    ).order_by('-race_date')[:2]
    
    # Get all completed races
    all_completed_races = Race.objects.filter(
        season=current_season,
        is_completed=True
    ).order_by('race_date')
    
    # Simple leaderboard based on total points
    leaderboard = Bet.objects.filter(
        race__season=current_season
    ).values('user__username').annotate(
        total_points=Sum('points')
    ).order_by('-total_points')[:10]
    
    # Create a dictionary to track position changes
    leaderboard_list = list(leaderboard)
    
    # Check if we have at least 2 races to compare positions
    if all_completed_races.count() >= 2:
        # Get the most recent race
        last_race = all_completed_races.last()
        
        # Get all races except the last one
        previous_races = all_completed_races.exclude(id=last_race.id)
        
        # Calculate previous standings (before the last race)
        previous_leaderboard = Bet.objects.filter(
            race__season=current_season,
            race__in=previous_races
        ).values('user__username').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Create a dictionary of previous positions
        previous_positions = {item['user__username']: i+1 for i, item in enumerate(previous_leaderboard)}
        
        # Now add position_change to each leaderboard item
        for i, item in enumerate(leaderboard_list):
            username = item['user__username']
            current_position = i + 1
            previous_position = previous_positions.get(username, 0)
            
            if previous_position == 0:
                item['position_change'] = "NEW"
            else:
                position_change = previous_position - current_position
                if position_change > 0:
                    item['position_change'] = f"+{position_change}"
                elif position_change < 0:
                    item['position_change'] = str(position_change)
                else:
                    item['position_change'] = "-"
    else:
        # If we don't have enough races, set all position changes to "-"
        for item in leaderboard_list:
            item['position_change'] = "-"
    
    # # Prepare data for classification line graph
    # classification_data, race_names = prepare_classification_graph_data(current_season)
    
    # # Convert classification data to JSON for template
    # classification_json = json.dumps({
    #     username: {
    #         'username': data['username'],
    #         'cumulative_points': data['cumulative_points']
    #     } for username, data in classification_data.items()
    # })
    
    # # Convert race names to JSON for template
    # race_names_json = json.dumps(race_names)
    
    # Get the last incomplete race for the superuser enter results button
    last_incomplete_race = Race.objects.filter(
        season=current_season,
        is_completed=False
    ).order_by('race_date').first()
    
    return render(request, 'betting/home.html', {
        'upcoming_races': upcoming_races,
        'completed_races': completed_races,
        'leaderboard': leaderboard,
        'position_changes': leaderboard_list,
        # 'classification_json': classification_json,
        # 'race_names_json': race_names_json,
        'last_incomplete_race': last_incomplete_race,
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
    race_names = [race.name for race in completed_races]  # Extract race names
    
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
                    'cumulative_points': [0] * len(completed_races),
                    'positions': [0] * len(completed_races)  # Add positions array
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
    
    # Calculate positions at each race
    for race_idx in range(len(completed_races)):
        # Sort users by cumulative points at this race
        sorted_users = sorted(
            classification_evolution.items(),
            key=lambda x: x[1]['cumulative_points'][race_idx],
            reverse=True
        )
        
        # Assign positions
        for position, (username, data) in enumerate(sorted_users, 1):
            data['positions'][race_idx] = position
    
    return classification_evolution, race_names


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

        # Create lists for podium comparisons in template
        quali_podium = [race_result.first_place_quali, race_result.second_place_quali, race_result.third_place_quali]
        race_podium = [race_result.first_place_race, race_result.second_place_race, race_result.third_place_race]
        
        # Calculate point breakdown for user bet
        quali_points = 0
        race_points = 0
        dnf_points = 0
        
        if user_bet:
            # Get point values based on race type
            point_values = race_result.get_point_values()
            podium_correct_position_points = point_values['PODIUM_CORRECT_POSITION']
            podium_wrong_position_points = point_values['PODIUM_WRONG_POSITION']
            dnf_correct_points = point_values['DNF_CORRECT']
            
            # Calculate QUALI points
            if user_bet.first_place_quali == race_result.first_place_quali:
                quali_points += podium_correct_position_points
            elif user_bet.first_place_quali in quali_podium:
                quali_points += podium_wrong_position_points
                
            if user_bet.second_place_quali == race_result.second_place_quali:
                quali_points += podium_correct_position_points
            elif user_bet.second_place_quali in quali_podium:
                quali_points += podium_wrong_position_points
                
            if user_bet.third_place_quali == race_result.third_place_quali:
                quali_points += podium_correct_position_points
            elif user_bet.third_place_quali in quali_podium:
                quali_points += podium_wrong_position_points
            
            # Calculate RACE points
            if user_bet.first_place_race == race_result.first_place_race:
                race_points += podium_correct_position_points
            elif user_bet.first_place_race in race_podium:
                race_points += podium_wrong_position_points
                
            if user_bet.second_place_race == race_result.second_place_race:
                race_points += podium_correct_position_points
            elif user_bet.second_place_race in race_podium:
                race_points += podium_wrong_position_points
                
            if user_bet.third_place_race == race_result.third_place_race:
                race_points += podium_correct_position_points
            elif user_bet.third_place_race in race_podium:
                race_points += podium_wrong_position_points
            
            # Calculate DNF points
            if user_bet.dnf_prediction == race_result.dnf_count:
                dnf_points = dnf_correct_points
        
        # Pass the point values to the template for display
        point_values = race_result.get_point_values()
        
        point_values = race_result.get_point_values()
        total_possible_points = (point_values['PODIUM_CORRECT_POSITION'] * 6) + point_values['DNF_CORRECT']

        context = {
            'race': race,
            'race_result': race_result,
            'user_bet': user_bet,
            'all_bets': all_bets,
            'quali_podium': quali_podium,
            'race_podium': race_podium,
            'quali_points': quali_points,
            'race_points': race_points,
            'dnf_points': dnf_points,
            'point_values': point_values,  # Pass the point values to the template
            'total_possible_points': total_possible_points
        }

        return render(request, 'betting/race_results.html', context)
    
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
    
    # Get all completed races for this season
    all_completed_races = Race.objects.filter(
        season=season,
        is_completed=True
    ).order_by('race_date')
    
    # Create a list from the standings queryset to modify it
    standings_list = list(standings)
    
    # Check if we have at least 2 races to compare positions
    if all_completed_races.count() >= 2:
        # Get the most recent race
        last_race = all_completed_races.last()
        
        # Get all races except the last one
        previous_races = all_completed_races.exclude(id=last_race.id)
        
        # Calculate previous standings (before the last race)
        previous_standings = Bet.objects.filter(
            race__season=season,
            race__in=previous_races
        ).values('user__username').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        # Create a dictionary of previous positions
        previous_positions = {item['user__username']: i+1 for i, item in enumerate(previous_standings)}
        
        # Now add position_change to each standings item
        for i, item in enumerate(standings_list):
            username = item['user__username']
            current_position = i + 1
            previous_position = previous_positions.get(username, 0)
            
            if previous_position == 0:
                item['position_change'] = "NEW"
            else:
                position_change = previous_position - current_position
                if position_change > 0:
                    item['position_change'] = f"+{position_change}"
                elif position_change < 0:
                    item['position_change'] = str(position_change)
                else:
                    item['position_change'] = "-"
    else:
        # If we don't have enough races, set all position changes to "-"
        for item in standings_list:
            item['position_change'] = "-"
    
    # Prepare data for classification line graph
    classification_data, race_names = prepare_classification_graph_data(season)
    
    # Convert classification data to JSON for template
    classification_json = json.dumps({
        username: {
            'username': data['username'],
            'cumulative_points': data['cumulative_points'],
            'positions': data['positions']  # Include positions data
        } for username, data in classification_data.items()
    })
    
    # Convert race names to JSON for template
    race_names_json = json.dumps(race_names)
    
    return render(request, 'betting/standings.html', {
        'season': season,
        'standings': standings_list,
        'all_seasons': all_seasons,
        'classification_json': classification_json,
        'race_names_json': race_names_json,
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
        
        # Create or update race result directly using the calculate_points_for_bets method
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
        
        # The points will be calculated automatically via the signal in models.py
        messages.success(request, "Race results saved and points calculated.")
        return redirect('race_detail', race_id=race.id)
    
    # Show form to enter results
    active_drivers = Driver.objects.filter(is_active=True)
    
    return render(request, 'betting/enter_results.html', {
        'race': race,
        'drivers': active_drivers,
    })

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
    
    return render(request, 'betting/login.html')

def rules_page(request):
    return render(request, 'betting/rules.html')

def all_races_view(request):
    # Get all races, ordered by date
    all_races = Race.objects.all().order_by('race_date')
    
    context = {
        'all_races': all_races
    }
    return render(request, 'betting/all_races.html', context)