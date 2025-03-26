from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Season(models.Model):
    year = models.IntegerField(unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.year} Season"

class Circuit(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Race(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='races')
    circuit = models.ForeignKey(Circuit, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "Monaco Grand Prix"
    race_date = models.DateTimeField()
    practice_start = models.DateTimeField()  # Betting deadline
    is_sprint = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    dnf_count = models.IntegerField(null=True, blank=True)  # Filled after race
    
    def __str__(self):
        return f"{self.name} - {self.season.year}"
    
    class Meta:
        ordering = ['race_date']

class Driver(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3)  # Three-letter code e.g., "HAM"
    team = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Bet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    race = models.ForeignKey(Race, on_delete=models.CASCADE, related_name='bets')
    first_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    second_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    third_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    first_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    second_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    third_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    dnf_prediction = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    points = models.FloatField(default=0.0)  # Points awarded after race
    extraPoints = models.FloatField(default=0.0) # Extra points (for example when user joins in the middle of the season)
    comments = models.TextField(blank=True, null=True)  # Reason for the extra points or any other admin comments

    def __str__(self):
        return f"{self.user.username}'s bet for {self.race}"
    
    class Meta:
        unique_together = ('user', 'race')  # One bet per race per user

class RaceResult(models.Model):
    race = models.OneToOneField(Race, on_delete=models.CASCADE, related_name='result')
    first_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    second_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    third_place_quali = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    first_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    second_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    third_place_race = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='+')
    dnf_count = models.IntegerField()
    
    def __str__(self):
        return f"Results for {self.race}"
    
    def calculate_points_for_bets(self):
        """Calculate points for all bets on this race."""
        bets = Bet.objects.filter(race=self.race)
        
        # Update race completed status and DNF count
        self.race.is_completed = True
        self.race.dnf_count = self.dnf_count
        self.race.save()
        
        if self.race.is_sprint:
            podium_correct_position_points = 1.5
            podium_wrong_position_points = 0.5
            dnf_points = 1
        else:
            podium_correct_position_points = 3
            podium_wrong_position_points = 1
            dnf_points = 2

        for bet in bets:
            points = 0

            # QUALI - Create lists of actual and predicted podium drivers
            actual_podium_quali = [self.first_place_quali, self.second_place_quali, self.third_place_quali]
            
            # Check for exact matches (right driver in right position: 3 points)
            if bet.first_place_quali == self.first_place_quali:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.first_place_quali in actual_podium_quali:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position
                
            if bet.second_place_quali == self.second_place_quali:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.second_place_quali in actual_podium_quali:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position
                
            if bet.third_place_quali == self.third_place_quali:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.third_place_quali in actual_podium_quali:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position

            # RACE - Create lists of actual and predicted podium drivers
            actual_podium = [self.first_place_race, self.second_place_race, self.third_place_race]
            
            # Check for exact matches (right driver in right position: 3 points)
            if bet.first_place_race == self.first_place_race:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.first_place_race in actual_podium:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position
                
            if bet.second_place_race == self.second_place_race:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.second_place_race in actual_podium:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position
                
            if bet.third_place_race == self.third_place_race:
                points += podium_correct_position_points  # 1 for being on podium + 2 for correct position
            elif bet.third_place_race in actual_podium:
                points += podium_wrong_position_points  # 1 for being on podium but wrong position
            
            # Check DNF prediction
            if bet.dnf_prediction == self.dnf_count:
                points += dnf_points
                
            # Update bet points (add eventual extra points)
            bet.points = points + bet.extraPoints
            bet.save()
        
        return bets.count()  # Return number of bets processed

# Signal to automatically calculate points when a RaceResult is created or updated
@receiver(post_save, sender=RaceResult)
def update_bet_points(sender, instance, created, **kwargs):
    """Update points for all bets when a race result is saved."""
    instance.calculate_points_for_bets()
