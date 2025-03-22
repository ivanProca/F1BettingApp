# betting/forms.py
from django import forms
from .models import Bet, Driver, User

class BetForm(forms.ModelForm):
    class Meta:
        model = Bet
        fields = ['first_place', 'second_place', 'third_place', 'dnf_prediction']
        
    def __init__(self, *args, **kwargs):
        super(BetForm, self).__init__(*args, **kwargs)
        # Only show active drivers in the dropdown
        active_drivers = Driver.objects.filter(is_active=True)
        self.fields['first_place'].queryset = active_drivers
        self.fields['second_place'].queryset = active_drivers
        self.fields['third_place'].queryset = active_drivers
        
    def clean(self):
        cleaned_data = super().clean()
        first = cleaned_data.get('first_place')
        second = cleaned_data.get('second_place')
        third = cleaned_data.get('third_place')
        
        # Check that user didn't select the same driver multiple times
        if first and second and first == second:
            raise forms.ValidationError("You can't select the same driver for first and second place.")
        if first and third and first == third:
            raise forms.ValidationError("You can't select the same driver for first and third place.")
        if second and third and second == third:
            raise forms.ValidationError("You can't select the same driver for second and third place.")
            
        return cleaned_data


from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']