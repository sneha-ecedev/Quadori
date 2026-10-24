import secrets
import string
import uuid
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from quadori.notifications import send_booking_confirmation, send_booking_sms
from quadori.city_data import INDIAN_CITY_NAMES
from mybookings.tickets import ticket_context

from .forms import FlightSearchForm, PassengerForm
from .models import Booking


SAMPLE_FLIGHTS = [
    {
        'id': 'ai201', 'airline': 'Air India', 'number': 'AI 201',
        'from': 'Delhi', 'to': 'Mumbai', 'departure': '06:15',
        'arrival': '08:25', 'duration': '2h 10m', 'price': Decimal('5499.00'),
    },
    {
        'id': '6e305', 'airline': 'IndiGo', 'number': '6E 305',
        'from': 'Delhi', 'to': 'Mumbai', 'departure': '08:40',
        'arrival': '10:55', 'duration': '2h 15m', 'price': Decimal('4899.00'),
    },
    {
        'id': 'uk941', 'airline': 'Vistara', 'number': 'UK 941',
        'from': 'Mumbai', 'to': 'Bengaluru', 'departure': '09:10',
        'arrival': '10:55', 'duration': '1h 45m', 'price': Decimal('6299.00'),
    },
    {
        'id': 'sg8721', 'airline': 'SpiceJet', 'number': 'SG 8721',
        'from': 'Delhi', 'to': 'Bengaluru', 'departure': '11:20',
        'arrival': '14:10', 'duration': '2h 50m', 'price': Decimal('5799.00'),
    },
    {
        'id': 'ai506', 'airline': 'Air India', 'number': 'AI 506',
        'from': 'Chennai', 'to': 'Delhi', 'departure': '07:00',
        'arrival': '09:50', 'duration': '2h 50m', 'price': Decimal('7199.00'),
    },
    {
        'id': '6e621', 'airline': 'IndiGo', 'number': '6E 621',
        'from': 'Hyderabad', 'to': 'Kolkata', 'departure': '13:35',
        'arrival': '15:45', 'duration': '2h 10m', 'price': Decimal('4599.00'),
    },
    {
        'id': 'uk955', 'airline': 'Vistara', 'number': 'UK 955',
        'from': 'Mumbai', 'to': 'Delhi', 'departure': '16:10',
        'arrival': '18:20', 'duration': '2h 10m', 'price': Decimal('6799.00'),
    },
    {
        'id': 'sg409', 'airline': 'SpiceJet', 'number': 'SG 409',
        'from': 'Pune', 'to': 'Bengaluru', 'departure': '10:25',
        'arrival': '12:00', 'duration': '1h 35m', 'price': Decimal('3899.00'),
    },
    {
        'id': 'ai628', 'airline': 'Air India', 'number': 'AI 628',
        'from': 'Ahmedabad', 'to': 'Mumbai', 'departure': '18:30',
        'arrival': '19:40', 'duration': '1h 10m', 'price': Decimal('4199.00'),
    },
    {
        'id': '6e772', 'airline': 'IndiGo', 'number': '6E 772',
        'from': 'Bengaluru', 'to': 'Chennai', 'departure': '20:05',
        'arrival': '21:10', 'duration': '1h 05m', 'price': Decimal('3499.00'),
    },
]

# Keep several fixed examples above, then cover every distinct supported route.
_flight_routes = {(item['from'], item['to']) for item in SAMPLE_FLIGHTS}
_airlines = ('Air India', 'IndiGo', 'SpiceJet', 'Akasa Air', 'Alliance Air')
for _route_index, (_origin, _destination) in enumerate(
    ((origin, destination) for origin in INDIAN_CITY_NAMES
     for destination in INDIAN_CITY_NAMES if destination != origin),
    start=1,
):
    if (_origin, _destination) in _flight_routes:
        continue
    _hour = 5 + (_route_index % 17)
    _duration_hours = 1 + (_route_index % 4)
    SAMPLE_FLIGHTS.append({
        'id': f'quadori-flight-{_route_index:04d}',
        'airline': _airlines[_route_index % len(_airlines)],
        'number': f'QF {_route_index:03d}',
        'from': _origin,
        'to': _destination,
        'departure': f'{_hour:02d}:00',
        'arrival': f'{(_hour + _duration_hours) % 24:02d}:20',
        'duration': f'{_duration_hours}h 20m',
        'price': Decimal(str(2499 + (_route_index % 12) * 350)),
    })


def search_flights(request):
    if request.GET:
        form = FlightSearchForm(request.GET)
        flights = []
        if form.is_valid():
            from_city = form.cleaned_data['from_city']
            to_city = form.cleaned_data['to_city']
            flights = [
                flight for flight in SAMPLE_FLIGHTS
                if flight['from'] == from_city and flight['to'] == to_city
            ]
            if not flights:
                messages.info(request, 'No sample flights were found for that route.')
        journey_date = form.cleaned_data.get('journey_date') if form.is_valid() else None
        passenger_count = form.cleaned_data.get('passengers', 1) if form.is_valid() else 1
    else:
        form = FlightSearchForm(initial={
            'journey_date': date.today(),
            'passengers': 1,
        })
        flights = SAMPLE_FLIGHTS[:10]
        journey_date = date.today()
        passenger_count = 1

    return render(request, 'flight/search.html', {
        'form': form,
        'flights': flights,
        'journey_date': journey_date,
        'passenger_count': passenger_count,
    })


def passenger_details(request):
    flight_id = request.POST.get('flight_id') if request.method == 'POST' else request.GET.get('flight_id')
    flight = next((item for item in SAMPLE_FLIGHTS if item['id'] == flight_id), None)
    if flight is None:
        raise Http404('Flight not found.')

    date_value = request.POST.get('journey_date') if request.method == 'POST' else request.GET.get('journey_date')
    journey_date = parse_date(date_value or '')
    try:
        passenger_count = int(
            request.POST.get('passenger_count') if request.method == 'POST'
            else request.GET.get('passengers', '1')
        )
    except (TypeError, ValueError):
        raise Http404('Invalid passenger count.')

    if journey_date is None or not 1 <= passenger_count <= 9:
        raise Http404('Invalid journey details.')

    PassengerFormSet = formset_factory(
        PassengerForm,
        extra=0,
        min_num=passenger_count,
        max_num=passenger_count,
        validate_min=True,
        validate_max=True,
    )
    formset = PassengerFormSet(request.POST or None)

    if (request.method == 'POST' and formset.is_valid()
            and len(formset.cleaned_data) == passenger_count):
        passenger_data = [form.cleaned_data for form in formset]
        total_price = flight['price'] * passenger_count
        booking = Booking.objects.create(
            booking_id=uuid.uuid4(),
            pnr_number=_generate_pnr(),
            user=request.user if request.user.is_authenticated else None,
            flight_date=journey_date,
            airline_name=flight['airline'],
            flight_number=flight['number'],
            from_city=flight['from'],
            to_city=flight['to'],
            departure_time=flight['departure'],
            arrival_time=flight['arrival'],
            duration=flight['duration'],
            passenger_count=passenger_count,
            passenger_details=passenger_data,
            total_price=total_price,
        )
        primary_passenger = passenger_data[0]
        send_booking_confirmation(
            recipient=primary_passenger['email'],
            customer_name=primary_passenger['full_name'],
            booking_id=booking.booking_id,
            reference=booking.pnr_number,
            service_name='Flight Booking',
            booking_date=booking.flight_date.strftime('%d %b %Y'),
            booking_time=f'{booking.departure_time} departure',
            amount=booking.total_price,
        )
        send_booking_sms(
            recipient=primary_passenger['phone_number'],
            customer_name=primary_passenger['full_name'],
            booking_id=booking.booking_id,
            reference=booking.pnr_number,
            service_name='Flight Booking',
            booking_date=booking.flight_date.strftime('%d %b %Y'),
            booking_time=f'{booking.departure_time} departure',
            amount=booking.total_price,
        )
        messages.success(request, 'Your flight booking was successful.')
        return redirect('flight:confirmation', booking_id=booking.booking_id)

    return render(request, 'flight/passengers.html', {
        'flight': flight,
        'journey_date': journey_date,
        'passenger_count': passenger_count,
        'formset': formset,
        'total_price': flight['price'] * passenger_count,
    })


def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    if booking.user_id and (
        not request.user.is_authenticated or booking.user_id != request.user.id
    ):
        raise Http404('Booking not found.')
    return render(request, 'flight/confirmation.html', {
        'booking': booking, **ticket_context('flight', booking),
    })


def _generate_pnr():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        pnr = ''.join(secrets.choice(alphabet) for _ in range(6))
        if not Booking.objects.filter(pnr_number=pnr).exists():
            return pnr
