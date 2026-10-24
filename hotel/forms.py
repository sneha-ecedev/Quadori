from django import forms
from django.utils import timezone
from quadori.city_data import INDIAN_CITY_CHOICES


HOTEL_CITIES = INDIAN_CITY_CHOICES

ROOM_TYPES = (
    ('Standard', 'Standard'),
    ('Deluxe', 'Deluxe'),
    ('Suite', 'Suite'),
)


class HotelSearchForm(forms.Form):
    city = forms.ChoiceField(
        choices=HOTEL_CITIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    check_in = forms.DateField(
        label='Check-in Date',
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )
    check_out = forms.DateField(
        label='Check-out Date',
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )
    adults = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=2,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 1, 'max': 8},
        ),
    )
    children = forms.IntegerField(
        min_value=0,
        max_value=8,
        initial=0,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 0, 'max': 8},
        ),
    )
    rooms = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=1,
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 1, 'max': 5},
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        adults = cleaned_data.get('adults')
        children = cleaned_data.get('children')
        if check_in and check_in < timezone.localdate():
            self.add_error('check_in', 'Check-in cannot be in the past.')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Check-out must be after check-in.')
        if adults is not None and children is not None and adults + children > 8:
            self.add_error('children', 'Adults and children together cannot exceed 8 guests.')
        return cleaned_data


class GuestForm(forms.Form):
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
