from django import forms
from quadori.city_data import INDIAN_CITY_CHOICES


INDIAN_CITIES = INDIAN_CITY_CHOICES


class FlightSearchForm(forms.Form):
    from_city = forms.ChoiceField(
        choices=INDIAN_CITIES,
        label='From City',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    to_city = forms.ChoiceField(
        choices=INDIAN_CITIES,
        label='To City',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    journey_date = forms.DateField(
        label='Journey Date',
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )
    passengers = forms.IntegerField(
        min_value=1,
        max_value=9,
        initial=1,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 1, 'max': 9},
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('from_city') == cleaned_data.get('to_city'):
            self.add_error('to_city', 'Choose a destination different from the origin.')
        return cleaned_data


class PassengerForm(forms.Form):
    GENDER_CHOICES = (
        ('', 'Select gender'),
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other'),
    )

    full_name = forms.CharField(
        max_length=150,
        label='Full Name',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    age = forms.IntegerField(
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 1, 'max': 120},
        ),
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    phone_number = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'tel'},
        ),
    )
