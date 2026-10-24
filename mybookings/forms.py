from django import forms


SERVICE_TYPES = (
    ('', 'All services'),
    ('flight', 'Flight'),
    ('bus', 'Bus'),
    ('train', 'Train'),
    ('hotel', 'Hotel'),
    ('restaurant', 'Restaurant'),
    ('movie', 'Movie'),
)


class BookingFilterForm(forms.Form):
    booking_id = forms.CharField(
        required=False,
        label='Booking ID',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by booking ID',
        }),
    )
    service_type = forms.ChoiceField(
        choices=SERVICE_TYPES,
        required=False,
        label='Service Type',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
