# betting/admin.py
from django.contrib import admin
from .models import Season, Circuit, Race, Driver, Bet, RaceResult

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('year', 'is_active')
    list_filter = ('is_active',)

@admin.register(Circuit)
class CircuitAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'country')
    search_fields = ('name', 'country')

@admin.register(Race)
class RaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'circuit', 'race_date', 'is_completed', 'is_sprint')
    list_filter = ('season', 'is_completed', 'is_sprint')
    search_fields = ('name',)
    date_hierarchy = 'race_date'

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'team', 'is_active')
    list_filter = ('team', 'is_active')
    search_fields = ('name', 'code')

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ('user', 'race', 'first_place_quali', 'second_place_quali', 'third_place_quali', 'first_place_race', 'second_place_race', 'third_place_race', 'dnf_prediction', 'points', 'extraPoints', 'comments')
    list_filter = ('race__season', 'race')
    search_fields = ('user__username',)

@admin.register(RaceResult)
class RaceResultAdmin(admin.ModelAdmin):
    list_display = ('race', 'first_place_quali', 'second_place_quali', 'third_place_quali', 'first_place_race', 'second_place_race', 'third_place_race', 'dnf_count')
    list_filter = ('race__season',)