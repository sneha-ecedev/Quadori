from django import forms
from django.utils import timezone


INDIAN_CITIES = (
    ('Mumbai', 'Mumbai'), ('Delhi', 'Delhi'), ('Bengaluru', 'Bengaluru'),
    ('Chennai', 'Chennai'), ('Hyderabad', 'Hyderabad'), ('Kolkata', 'Kolkata'),
    ('Jaipur', 'Jaipur'), ('Pune', 'Pune'), ('Ahmedabad', 'Ahmedabad'),
    ('Kochi', 'Kochi'),
)

THEATRE_FILTERS = (
    ('PVR', 'PVR'), ('INOX', 'INOX'), ('Cinepolis', 'Cinepolis'),
    ('AGS', 'AGS'), ('Sathyam', 'Sathyam'),
)


class MovieSearchForm(forms.Form):
    city = forms.ChoiceField(
        choices=(('', 'All cities'), *INDIAN_CITIES), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    theatre = forms.ChoiceField(
        choices=(('', 'All theatres'), *THEATRE_FILTERS), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    show_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
            'min': timezone.localdate().isoformat(),
        }),
    )

    def clean_show_date(self):
        show_date = self.cleaned_data.get('show_date')
        if show_date and show_date < timezone.localdate():
            raise forms.ValidationError('Choose today or a future date.')
        return show_date


class CustomerDetailsForm(forms.Form):
    customer_name = forms.CharField(
        max_length=150,
        label='Full name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}),
    )
    customer_email = forms.EmailField(
        label='Email address',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    customer_phone = forms.CharField(
        max_length=20,
        label='Phone number',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'type': 'tel', 'autocomplete': 'tel',
            'pattern': r'[+0-9 ()-]{7,20}',
        }),
    )
