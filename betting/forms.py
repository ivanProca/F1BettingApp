# betting/forms.py
from django import forms
from .models import Bet, Driver, User

class BetForm(forms.ModelForm):
    class Meta:
        model = Bet
        fields = ['first_place_quali', 'second_place_quali', 'third_place_quali', 'first_place_race', 'second_place_race', 'third_place_race', 'dnf_prediction']
        
    def __init__(self, *args, **kwargs):
        super(BetForm, self).__init__(*args, **kwargs)
        # Only show active drivers in the dropdown
        active_drivers = Driver.objects.filter(is_active=True)

        self.fields['first_place_quali'].queryset = active_drivers
        self.fields['second_place_quali'].queryset = active_drivers
        self.fields['third_place_quali'].queryset = active_drivers

        self.fields['first_place_race'].queryset = active_drivers
        self.fields['second_place_race'].queryset = active_drivers
        self.fields['third_place_race'].queryset = active_drivers
        
    def clean(self):
        cleaned_data = super().clean()
        
        first_quali = cleaned_data.get('first_place_quali')
        second_quali = cleaned_data.get('second_place_quali')
        third_quali = cleaned_data.get('third_place_quali')

        first_race = cleaned_data.get('first_place_race')
        second_race = cleaned_data.get('second_place_race')
        third_race = cleaned_data.get('third_place_race')
        
        # Check that user didn't select the same driver multiple times
        if first_quali and second_quali and first_quali == second_quali:
            raise forms.ValidationError("You can't select the same driver for first and second place.")
        if first_quali and third_quali and first_quali == third_quali:
            raise forms.ValidationError("You can't select the same driver for first and third place.")
        if second_quali and third_quali and second_quali == third_quali:
            raise forms.ValidationError("You can't select the same driver for second and third place.")

        if first_race and second_race and first_race == second_race:
            raise forms.ValidationError("You can't select the same driver for first and second place.")
        if first_race and third_race and first_race == third_race:
            raise forms.ValidationError("You can't select the same driver for first and third place.")
        if second_race and third_race and second_race == third_race:
            raise forms.ValidationError("You can't select the same driver for second and third place.")
            
        return cleaned_data


from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']