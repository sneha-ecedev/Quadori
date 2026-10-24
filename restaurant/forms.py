from django import forms
from django.utils import timezone
from quadori.city_data import INDIAN_CITY_CHOICES


INDIAN_CITIES = INDIAN_CITY_CHOICES

CUISINES = (
    ('', 'All cuisines'),
    ('South Indian', 'South Indian'),
    ('North Indian', 'North Indian'),
    ('Chinese', 'Chinese'),
    ('Italian', 'Italian'),
    ('Fast Food', 'Fast Food'),
)


class RestaurantSearchForm(forms.Form):
    city = forms.ChoiceField(
        choices=INDIAN_CITIES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cuisine = forms.ChoiceField(
        choices=CUISINES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    booking_date = forms.DateField(
        label='Booking Date',
        widget=forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'},
            format='%Y-%m-%d',
        ),
        input_formats=['%Y-%m-%d'],
    )
    booking_time = forms.TimeField(
        label='Booking Time',
        widget=forms.TimeInput(
            attrs={'class': 'form-control', 'type': 'time'},
            format='%H:%M',
        ),
        input_formats=['%H:%M'],
    )
    guests = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=2,
        label='Number of Guests',
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'min': 1, 'max': 20},
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')
        if booking_date and booking_date < timezone.localdate():
            self.add_error('booking_date', 'Booking date cannot be in the past.')
        if (
            booking_date == timezone.localdate()
            and booking_time
            and booking_time <= timezone.localtime().time().replace(second=0, microsecond=0)
        ):
            self.add_error('booking_time', 'Choose a future time for today.')
        return cleaned_data


class CustomerDetailsForm(forms.Form):
    customer_name = forms.CharField(
        max_length=150,
        label='Customer Name',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    customer_phone = forms.CharField(
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'type': 'tel'},
        ),
    )
    customer_email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
