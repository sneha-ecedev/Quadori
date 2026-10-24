from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date

from quadori.notifications import send_booking_confirmation, send_booking_sms
from quadori.city_data import INDIAN_CITY_NAMES
from mybookings.tickets import ticket_context

from .forms import BusSearchForm, PassengerForm
from .models import BusBooking, ReservedSeat


SAMPLE_BUSES = [
    {
        'id': 'redbus-del-mum-01', 'operator': 'Volvo Express',
        'number': 'DL 01 AB 4821', 'type': 'AC Sleeper',
        'source': 'Delhi', 'destination': 'Mumbai', 'departure': '18:30',
        'arrival': '08:00', 'duration': '13h 30m', 'fare': Decimal('1899.00'),
    },
    {
        'id': 'orange-mum-pun-02', 'operator': 'Orange Travels',
        'number': 'MH 12 CD 7350', 'type': 'AC Semi-Sleeper',
        'source': 'Mumbai', 'destination': 'Pune', 'departure': '07:15',
        'arrival': '10:45', 'duration': '3h 30m', 'fare': Decimal('699.00'),
    },
    {
        'id': 'srs-ben-hyd-03', 'operator': 'SRS Travels',
        'number': 'KA 03 EF 2194', 'type': 'AC Sleeper',
        'source': 'Bengaluru', 'destination': 'Hyderabad', 'departure': '20:00',
        'arrival': '06:30', 'duration': '10h 30m', 'fare': Decimal('1299.00'),
    },
    {
        'id': 'tnstc-che-ben-04', 'operator': 'National Travels',
        'number': 'TN 01 GH 6012', 'type': 'AC Seater',
        'source': 'Chennai', 'destination': 'Bengaluru', 'departure': '06:00',
        'arrival': '12:00', 'duration': '6h 00m', 'fare': Decimal('899.00'),
    },
    {
        'id': 'rj-del-jai-05', 'operator': 'Rajasthan Roadways',
        'number': 'RJ 14 JK 3478', 'type': 'Non-AC Seater',
        'source': 'Delhi', 'destination': 'Jaipur', 'departure': '09:00',
        'arrival': '14:30', 'duration': '5h 30m', 'fare': Decimal('499.00'),
    },
    {
        'id': 'gs-goa-mum-06', 'operator': 'Goa Shuttle',
        'number': 'GA 07 LM 8840', 'type': 'AC Sleeper',
        'source': 'Goa', 'destination': 'Mumbai', 'departure': '19:45',
        'arrival': '07:15', 'duration': '11h 30m', 'fare': Decimal('1499.00'),
    },
    {
        'id': 'green-kol-hyd-07', 'operator': 'GreenLine Travels',
        'number': 'WB 19 NP 2256', 'type': 'AC Sleeper',
        'source': 'Kolkata', 'destination': 'Hyderabad', 'departure': '17:00',
        'arrival': '12:00', 'duration': '19h 00m', 'fare': Decimal('2199.00'),
    },
    {
        'id': 'guj-ahm-mum-08', 'operator': 'Gujarat Express Bus',
        'number': 'GJ 01 QR 9051', 'type': 'AC Seater',
        'source': 'Ahmedabad', 'destination': 'Mumbai', 'departure': '21:00',
        'arrival': '07:00', 'duration': '10h 00m', 'fare': Decimal('1199.00'),
    },
    {
        'id': 'orange-hyd-ben-09', 'operator': 'Orange Travels',
        'number': 'TS 09 ST 4317', 'type': 'AC Sleeper',
        'source': 'Hyderabad', 'destination': 'Bengaluru', 'departure': '22:15',
        'arrival': '07:15', 'duration': '9h 00m', 'fare': Decimal('1399.00'),
    },
    {
        'id': 'msrtc-pun-goa-10', 'operator': 'Maharashtra Travels',
        'number': 'MH 14 UV 6632', 'type': 'AC Semi-Sleeper',
        'source': 'Pune', 'destination': 'Goa', 'departure': '20:30',
        'arrival': '07:30', 'duration': '11h 00m', 'fare': Decimal('1099.00'),
    },
]

_bus_routes = {(item['source'], item['destination']) for item in SAMPLE_BUSES}
_bus_operators = ('Quadori Roadways', 'InterCity Travels', 'National Express', 'CityLink')
_bus_types = ('AC Sleeper', 'AC Semi-Sleeper', 'AC Seater', 'Non-AC Sleeper')
for _route_index, (_origin, _destination) in enumerate(
    ((origin, destination) for origin in INDIAN_CITY_NAMES
     for destination in INDIAN_CITY_NAMES if destination != origin),
    start=1,
):
    if (_origin, _destination) in _bus_routes:
        continue
    _hour = 5 + (_route_index % 18)
    _duration_hours = 3 + (_route_index % 19)
    SAMPLE_BUSES.append({
        'id': f'quadori-bus-{_route_index:04d}',
        'operator': _bus_operators[_route_index % len(_bus_operators)],
        'number': f'QB {_route_index:04d}',
        'type': _bus_types[_route_index % len(_bus_types)],
        'source': _origin,
        'destination': _destination,
        'departure': f'{_hour:02d}:00',
        'arrival': f'{(_hour + _duration_hours) % 24:02d}:30',
        'duration': f'{_duration_hours}h 30m',
        'fare': Decimal(str(399 + (_route_index % 15) * 150)),
    })

SEAT_NUMBERS = [
    f'{row}{letter}'
    for row in range(1, 9)
    for letter in 'ABCD'
]


@login_required(login_url='accounts:login')
def search_buses(request):
    if request.GET:
        form = BusSearchForm(request.GET)
        buses = []
        if form.is_valid():
            source = form.cleaned_data['source']
            destination = form.cleaned_data['destination']
            journey_date = form.cleaned_data['journey_date']
            passengers = form.cleaned_data['passengers']
            buses = [
                bus for bus in SAMPLE_BUSES
                if bus['source'] == source and bus['destination'] == destination
            ]
        else:
            journey_date = None
            passengers = 1
    else:
        journey_date = date.today()
        passengers = 1
        form = BusSearchForm(initial={
            'journey_date': journey_date,
            'passengers': passengers,
        })
        buses = SAMPLE_BUSES[:10]

    for bus in buses:
        bus['available_seats'] = len(SEAT_NUMBERS) - len(
            _reserved_seat_numbers(bus['id'], journey_date)
        ) if journey_date else len(SEAT_NUMBERS)

    return render(request, 'bus/search.html', {
        'form': form,
        'buses': buses,
        'journey_date': journey_date,
        'passengers': passengers,
    })


@login_required(login_url='accounts:login')
def book_bus(request):
    bus_code = request.POST.get('bus_code') if request.method == 'POST' else request.GET.get('bus_code')
    bus = next((item for item in SAMPLE_BUSES if item['id'] == bus_code), None)
    if bus is None:
        raise Http404('Bus not found.')

    date_value = request.POST.get('journey_date') if request.method == 'POST' else request.GET.get('journey_date')
    journey_date = parse_date(date_value or '')
    count_value = request.POST.get('passenger_count') if request.method == 'POST' else request.GET.get('passengers', '1')
    try:
        passenger_count = int(count_value)
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
    reserved_seats = _reserved_seat_numbers(bus['id'], journey_date)
    selected_seats = request.POST.getlist('seats') if request.method == 'POST' else []
    seat_error = ''

    if (request.method == 'POST' and formset.is_valid()
            and len(formset.cleaned_data) == passenger_count):
        if len(selected_seats) != passenger_count or len(set(selected_seats)) != passenger_count:
            seat_error = f'Select exactly {passenger_count} different seats.'
        elif any(seat not in SEAT_NUMBERS for seat in selected_seats):
            seat_error = 'One or more selected seats are invalid.'
        elif any(seat in reserved_seats for seat in selected_seats):
            seat_error = 'A selected seat was just booked. Please choose available seats.'
        else:
            ordered_selected_seats = sorted(selected_seats, key=SEAT_NUMBERS.index)
            passenger_data = [
                {**passenger_form.cleaned_data, 'seat_number': seat_number}
                for passenger_form, seat_number in zip(formset, ordered_selected_seats)
            ]
            try:
                with transaction.atomic():
                    booking = BusBooking.objects.create(
                        user=request.user,
                        bus_code=bus['id'],
                        operator=bus['operator'],
                        bus_number=bus['number'],
                        bus_type=bus['type'],
                        source=bus['source'],
                        destination=bus['destination'],
                        journey_date=journey_date,
                        departure_time=bus['departure'],
                        arrival_time=bus['arrival'],
                        duration=bus['duration'],
                        seat_count=passenger_count,
                        passenger_details=passenger_data,
                        fare_per_seat=bus['fare'],
                        total_fare=bus['fare'] * passenger_count,
                    )
                    ReservedSeat.objects.bulk_create([
                        ReservedSeat(
                            booking=booking,
                            bus_code=bus['id'],
                            journey_date=journey_date,
                            seat_number=seat,
                        )
                        for seat in ordered_selected_seats
                    ])
                primary_passenger = booking.passenger_details[0]
                send_booking_confirmation(
                    recipient=primary_passenger['email'],
                    customer_name=primary_passenger['full_name'],
                    booking_id=booking.booking_id,
                    reference=f'BUS-{booking.booking_id.hex[:10].upper()}',
                    service_name='Bus Booking',
                    booking_date=booking.journey_date.strftime('%d %b %Y'),
                    booking_time=f'{booking.departure_time} departure',
                    amount=booking.total_fare,
                )
                send_booking_sms(
                    recipient=primary_passenger['phone_number'],
                    customer_name=primary_passenger['full_name'],
                    booking_id=booking.booking_id,
                    reference=f'BUS-{booking.booking_id.hex[:10].upper()}',
                    service_name='Bus Booking',
                    booking_date=booking.journey_date.strftime('%d %b %Y'),
                    booking_time=f'{booking.departure_time} departure',
                    amount=booking.total_fare,
                )
                return redirect('bus:confirmation', booking_id=booking.booking_id)
            except IntegrityError:
                seat_error = 'A selected seat was just booked. Please choose available seats.'
                reserved_seats = _reserved_seat_numbers(bus['id'], journey_date)

    seat_layout = [
        {
            'number': seat,
            'reserved': seat in reserved_seats,
            'selected': seat in selected_seats,
        }
        for seat in SEAT_NUMBERS
    ]
    return render(request, 'bus/booking.html', {
        'bus': bus,
        'journey_date': journey_date,
        'passenger_count': passenger_count,
        'formset': formset,
        'seat_layout': seat_layout,
        'seat_error': seat_error,
        'total_fare': bus['fare'] * passenger_count,
    })


@login_required(login_url='accounts:login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        BusBooking.objects.prefetch_related('reserved_seats'),
        booking_id=booking_id,
        user=request.user,
    )
    return render(request, 'bus/confirmation.html', {
        'booking': booking, **ticket_context('bus', booking),
    })


def _reserved_seat_numbers(bus_code, journey_date):
    return set(
        ReservedSeat.objects.filter(
            bus_code=bus_code,
            journey_date=journey_date,
        ).values_list('seat_number', flat=True)
    )
