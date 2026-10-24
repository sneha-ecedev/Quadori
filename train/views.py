import secrets
import string
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from quadori.notifications import send_booking_confirmation, send_booking_sms
from quadori.city_data import INDIAN_CITY_NAMES
from mybookings.tickets import ticket_context

from .forms import PassengerForm, TrainSearchForm
from .models import ReservedSeat, TrainBooking


FARE_MULTIPLIERS = {
    'Sleeper': Decimal('1.00'),
    '3A': Decimal('1.80'),
    '2A': Decimal('2.50'),
    '1A': Decimal('4.00'),
}

SAMPLE_TRAINS = [
    {
        'id': 'rajdhani-del-mum', 'number': '12952', 'name': 'Mumbai Rajdhani Express',
        'source': 'Delhi', 'destination': 'Mumbai', 'departure': '16:55',
        'arrival': '08:35', 'duration': '15h 40m', 'base_fare': Decimal('1450.00'),
    },
    {
        'id': 'shatabdi-del-jaipur', 'number': '12015', 'name': 'Ajmer Shatabdi Express',
        'source': 'Delhi', 'destination': 'Jaipur', 'departure': '06:10',
        'arrival': '10:40', 'duration': '4h 30m', 'base_fare': Decimal('520.00'),
    },
    {
        'id': 'duronto-mum-pun', 'number': '12263', 'name': 'Pune Duronto Express',
        'source': 'Mumbai', 'destination': 'Pune', 'departure': '23:10',
        'arrival': '02:35', 'duration': '3h 25m', 'base_fare': Decimal('410.00'),
    },
    {
        'id': 'brindavan-che-ben', 'number': '12639', 'name': 'Brindavan Express',
        'source': 'Chennai', 'destination': 'Bengaluru', 'departure': '07:50',
        'arrival': '13:25', 'duration': '5h 35m', 'base_fare': Decimal('350.00'),
    },
    {
        'id': 'charminar-hyd-che', 'number': '12760', 'name': 'Charminar Express',
        'source': 'Hyderabad', 'destination': 'Chennai', 'departure': '18:10',
        'arrival': '07:30', 'duration': '13h 20m', 'base_fare': Decimal('610.00'),
    },
    {
        'id': 'howrah-del-kol', 'number': '12302', 'name': 'Howrah Rajdhani Express',
        'source': 'Delhi', 'destination': 'Kolkata', 'departure': '16:50',
        'arrival': '09:55', 'duration': '17h 05m', 'base_fare': Decimal('1590.00'),
    },
    {
        'id': 'goa-mum-goa', 'number': '10103', 'name': 'Mandovi Express',
        'source': 'Mumbai', 'destination': 'Goa', 'departure': '07:10',
        'arrival': '18:45', 'duration': '11h 35m', 'base_fare': Decimal('470.00'),
    },
    {
        'id': 'sabarmati-ahm-jaipur', 'number': '12216', 'name': 'Garib Rath Express',
        'source': 'Ahmedabad', 'destination': 'Jaipur', 'departure': '19:30',
        'arrival': '07:15', 'duration': '11h 45m', 'base_fare': Decimal('680.00'),
    },
    {
        'id': 'kashi-del-var', 'number': '15128', 'name': 'Kashi Vishwanath Express',
        'source': 'Delhi', 'destination': 'Varanasi', 'departure': '11:35',
        'arrival': '23:55', 'duration': '12h 20m', 'base_fare': Decimal('560.00'),
    },
    {
        'id': 'gomti-luc-del', 'number': '12419', 'name': 'Gomti Express',
        'source': 'Lucknow', 'destination': 'Delhi', 'departure': '06:00',
        'arrival': '14:00', 'duration': '8h 00m', 'base_fare': Decimal('430.00'),
    },
]

_train_routes = {(item['source'], item['destination']) for item in SAMPLE_TRAINS}
_train_names = ('Intercity Express', 'Jan Shatabdi', 'Superfast Express', 'Regional Express')
for _route_index, (_origin, _destination) in enumerate(
    ((origin, destination) for origin in INDIAN_CITY_NAMES
     for destination in INDIAN_CITY_NAMES if destination != origin),
    start=1,
):
    if (_origin, _destination) in _train_routes:
        continue
    _hour = 4 + (_route_index % 19)
    _duration_hours = 2 + (_route_index % 22)
    SAMPLE_TRAINS.append({
        'id': f'quadori-train-{_route_index:04d}',
        'number': f'{90000 + _route_index:05d}',
        'name': f'{_train_names[_route_index % len(_train_names)]} {_origin}-{_destination}',
        'source': _origin,
        'destination': _destination,
        'departure': f'{_hour:02d}:00',
        'arrival': f'{(_hour + _duration_hours) % 24:02d}:15',
        'duration': f'{_duration_hours}h 15m',
        'base_fare': Decimal(str(180 + (_route_index % 20) * 45)),
    })

SEAT_NUMBERS = [
    f'{row:02d}{letter}'
    for row in range(1, 13)
    for letter in 'ABC'
]


def _fare_for(train, travel_class):
    return train['base_fare'] * FARE_MULTIPLIERS[travel_class]


@login_required(login_url='accounts:login')
def search_trains(request):
    if request.GET:
        form = TrainSearchForm(request.GET)
        trains = []
        if form.is_valid():
            source = form.cleaned_data['source']
            destination = form.cleaned_data['destination']
            journey_date = form.cleaned_data['journey_date']
            travel_class = form.cleaned_data['travel_class']
            passengers = form.cleaned_data['passengers']
            trains = [
                train for train in SAMPLE_TRAINS
                if train['source'] == source and train['destination'] == destination
            ]
        else:
            journey_date = None
            travel_class = 'Sleeper'
            passengers = 1
    else:
        journey_date = date.today()
        travel_class = 'Sleeper'
        passengers = 1
        form = TrainSearchForm(initial={
            'journey_date': journey_date,
            'travel_class': travel_class,
            'passengers': passengers,
        })
        trains = SAMPLE_TRAINS[:10]

    for train in trains:
        train['fare'] = _fare_for(train, travel_class)
        train['available_seats'] = len(SEAT_NUMBERS) - len(
            _reserved_seat_numbers(train['id'], journey_date, travel_class)
        ) if journey_date else len(SEAT_NUMBERS)

    return render(request, 'train/search.html', {
        'form': form,
        'trains': trains,
        'journey_date': journey_date,
        'travel_class': travel_class,
        'passengers': passengers,
    })


@login_required(login_url='accounts:login')
def book_train(request):
    train_code = request.POST.get('train_code') if request.method == 'POST' else request.GET.get('train_code')
    train = next((item for item in SAMPLE_TRAINS if item['id'] == train_code), None)
    if train is None:
        raise Http404('Train not found.')

    date_value = request.POST.get('journey_date') if request.method == 'POST' else request.GET.get('journey_date')
    journey_date = parse_date(date_value or '')
    class_value = request.POST.get('travel_class') if request.method == 'POST' else request.GET.get('travel_class', 'Sleeper')
    count_value = request.POST.get('passenger_count') if request.method == 'POST' else request.GET.get('passengers', '1')
    try:
        passenger_count = int(count_value)
    except (TypeError, ValueError):
        raise Http404('Invalid passenger count.')
    if journey_date is None or not 1 <= passenger_count <= 9 or class_value not in FARE_MULTIPLIERS:
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
    reserved_seats = _reserved_seat_numbers(train['id'], journey_date, class_value)
    selected_seats = request.POST.getlist('seats') if request.method == 'POST' else []
    seat_error = ''
    fare = _fare_for(train, class_value)

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
                    booking = TrainBooking.objects.create(
                        pnr_number=_generate_pnr(),
                        user=request.user,
                        train_code=train['id'],
                        train_number=train['number'],
                        train_name=train['name'],
                        source=train['source'],
                        destination=train['destination'],
                        journey_date=journey_date,
                        travel_class=class_value,
                        departure_time=train['departure'],
                        arrival_time=train['arrival'],
                        duration=train['duration'],
                        passenger_count=passenger_count,
                        passenger_details=passenger_data,
                        fare_per_passenger=fare,
                        total_fare=fare * passenger_count,
                    )
                    ReservedSeat.objects.bulk_create([
                        ReservedSeat(
                            booking=booking,
                            train_code=train['id'],
                            journey_date=journey_date,
                            travel_class=class_value,
                            seat_number=seat,
                        )
                        for seat in ordered_selected_seats
                    ])
                primary_passenger = booking.passenger_details[0]
                send_booking_confirmation(
                    recipient=primary_passenger['email'],
                    customer_name=primary_passenger['full_name'],
                    booking_id=booking.booking_id,
                    reference=booking.pnr_number,
                    service_name='Train Booking',
                    booking_date=booking.journey_date.strftime('%d %b %Y'),
                    booking_time=f'{booking.departure_time} departure',
                    amount=booking.total_fare,
                )
                send_booking_sms(
                    recipient=primary_passenger['phone_number'],
                    customer_name=primary_passenger['full_name'],
                    booking_id=booking.booking_id,
                    reference=booking.pnr_number,
                    service_name='Train Booking',
                    booking_date=booking.journey_date.strftime('%d %b %Y'),
                    booking_time=f'{booking.departure_time} departure',
                    amount=booking.total_fare,
                )
                return redirect('train:confirmation', booking_id=booking.booking_id)
            except IntegrityError:
                seat_error = 'A selected seat was just booked. Please choose available seats.'
                reserved_seats = _reserved_seat_numbers(train['id'], journey_date, class_value)

    seat_layout = [
        {
            'number': seat,
            'reserved': seat in reserved_seats,
            'selected': seat in selected_seats,
        }
        for seat in SEAT_NUMBERS
    ]
    return render(request, 'train/booking.html', {
        'train': train,
        'journey_date': journey_date,
        'travel_class': class_value,
        'passenger_count': passenger_count,
        'formset': formset,
        'seat_layout': seat_layout,
        'seat_error': seat_error,
        'fare': fare,
        'total_fare': fare * passenger_count,
    })


@login_required(login_url='accounts:login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        TrainBooking.objects.prefetch_related('reserved_seats'),
        booking_id=booking_id,
        user=request.user,
    )
    return render(request, 'train/confirmation.html', {
        'booking': booking, **ticket_context('train', booking),
    })


def _reserved_seat_numbers(train_code, journey_date, travel_class):
    return set(
        ReservedSeat.objects.filter(
            train_code=train_code,
            journey_date=journey_date,
            travel_class=travel_class,
        ).values_list('seat_number', flat=True)
    )


def _generate_pnr():
    while True:
        pnr = ''.join(secrets.choice(string.digits) for _ in range(10))
        if not TrainBooking.objects.filter(pnr_number=pnr).exists():
            return pnr
