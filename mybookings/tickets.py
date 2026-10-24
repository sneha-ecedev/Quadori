import base64
import io
import json
from decimal import Decimal

import qrcode

from bus.models import BusBooking
from flight.models import Booking as FlightBooking
from hotel.models import HotelBooking
from movie.models import MovieBooking
from restaurant.models import RestaurantBooking
from train.models import TrainBooking


TICKET_SOURCES = {
    'flight': (FlightBooking, 'Flight'),
    'bus': (BusBooking, 'Bus'),
    'train': (TrainBooking, 'Train'),
    'hotel': (HotelBooking, 'Hotel'),
    'restaurant': (RestaurantBooking, 'Restaurant'),
    'movie': (MovieBooking, 'Movie'),
}


def ticket_context(service_key, booking):
    qr_bytes = _qr_bytes(_qr_payload(service_key, booking))
    encoded = base64.b64encode(qr_bytes).decode('ascii')
    from django.urls import reverse
    return {
        'ticket_qr_data_uri': f'data:image/png;base64,{encoded}',
        'ticket_download_url': reverse('mybookings:ticket', kwargs={
            'service_key': service_key, 'booking_id': booking.booking_id,
        }),
    }


def build_ticket_pdf(service_key, booking):
    data = _ticket_data(service_key, booking)
    from .pdf_templates import bus, flight, hotel, movie, restaurant, train
    renderers = {
        'flight': flight.render, 'bus': bus.render, 'train': train.render,
        'hotel': hotel.render, 'restaurant': restaurant.render,
        'movie': movie.render,
    }
    return renderers[service_key](booking, data, _qr_bytes(_qr_payload(service_key, booking)))


def _qr_payload(service_key, booking):
    data = _ticket_data(service_key, booking)
    return json.dumps({
        'booking_id': data['booking_id'], 'booking_number': data['reference'],
        'customer_name': data['customer'], 'service_name': data['service'],
        'booking_status': data['status'],
    }, ensure_ascii=False, separators=(',', ':'))


def _qr_bytes(payload):
    image = qrcode.make(payload)
    result = io.BytesIO()
    image.save(result, format='PNG')
    return result.getvalue()


def _ticket_data(service_key, booking):
    service = TICKET_SOURCES[service_key][1]
    booking_id = str(booking.booking_id)
    status = booking.get_status_display()
    booking_date = booking.created_at.strftime('%d %b %Y, %I:%M %p')
    details = []
    people = []
    if service_key == 'flight':
        reference = booking.pnr_number
        passengers = booking.passenger_details or []
        customer = _first_name(passengers, booking.user)
        details = [('Airline / Flight', f'{booking.airline_name} / {booking.flight_number}'),
                   ('Route', f'{booking.from_city} to {booking.to_city}'),
                   ('Journey Date', booking.flight_date.strftime('%d %b %Y')),
                   ('Time', f'{booking.departure_time} - {booking.arrival_time}'),
                   ('Seats', 'Not assigned'), ('Amount', _money(booking.total_price))]
        people = [_person_line(p, i, 'Passenger') for i, p in enumerate(passengers, 1)]
    elif service_key == 'bus':
        reference = f'BUS-{booking.booking_id.hex[:10].upper()}'
        passengers = booking.passenger_details or []
        customer = _first_name(passengers, booking.user)
        details = [('Bus / Operator', f'{booking.bus_number} / {booking.operator}'),
                   ('Route', f'{booking.source} to {booking.destination}'),
                   ('Journey Date', booking.journey_date.strftime('%d %b %Y')),
                   ('Time', f'{booking.departure_time} - {booking.arrival_time}'),
                   ('Seats', ', '.join(_reserved_or_passenger_seats(booking, passengers, 'bus')) or 'Not assigned'),
                   ('Amount', _money(booking.total_fare))]
        people = [_person_line(p, i, 'Passenger') for i, p in enumerate(passengers, 1)]
    elif service_key == 'train':
        reference = booking.pnr_number
        passengers = booking.passenger_details or []
        customer = _first_name(passengers, booking.user)
        details = [('Train', f'{booking.train_name} / {booking.train_number}'),
                   ('Route', f'{booking.source} to {booking.destination}'),
                   ('Class', booking.travel_class), ('Journey Date', booking.journey_date.strftime('%d %b %Y')),
                   ('Time', f'{booking.departure_time} - {booking.arrival_time}'),
                   ('Berths', ', '.join(_reserved_or_passenger_seats(booking, passengers, 'train')) or 'Not assigned'),
                   ('Amount', _money(booking.total_fare))]
        people = [_person_line(p, i, 'Passenger') for i, p in enumerate(passengers, 1)]
    elif service_key == 'hotel':
        reference = f'HTL-{booking.booking_id.hex[:10].upper()}'
        guests = booking.guest_details or []
        customer = _first_name(guests, booking.user)
        details = [('Hotel', booking.hotel_name), ('Address', f'{booking.address}, {booking.city}'),
                   ('Stay', f'{booking.check_in:%d %b %Y} to {booking.check_out:%d %b %Y} ({booking.nights} nights)'),
                   ('Time', 'Check-in time to be confirmed with the hotel'),
                   ('Rooms', f'{booking.room_count} x {booking.room_type}'),
                   ('Amount', _money(booking.total_price))]
        people = [_person_line(p, i, 'Guest') for i, p in enumerate(guests, 1)]
    elif service_key == 'restaurant':
        reference = f'RST-{booking.booking_id.hex[:10].upper()}'
        customer = booking.customer_name
        details = [('Restaurant', booking.restaurant_name), ('Address', f'{booking.address}, {booking.city}'),
                   ('Journey Date', booking.booking_date.strftime('%d %b %Y')),
                   ('Time', booking.booking_time.strftime('%I:%M %p')),
                   ('Table / Guests', f'{booking.guest_count} guests'),
                   ('Amount', _money(booking.average_cost * booking.guest_count))]
        people = [f"{booking.customer_name} · {booking.customer_email} · {booking.customer_phone}"]
    else:
        reference = booking.booking_number
        customer = booking.customer_name
        seats = booking.seat_numbers or list(booking.reserved_seats.values_list('seat_number', flat=True))
        details = [('Movie', booking.movie_name), ('Theatre', f'{booking.theatre_name}, {booking.city}'),
                   ('Journey Date', booking.show_date.strftime('%d %b %Y')), ('Time', booking.show_time),
                   ('Seats', ', '.join(seats) or 'Not assigned'), ('Amount', _money(booking.total_amount))]
        people = [f"{booking.customer_name} · {booking.customer_email} · {booking.customer_phone}"]
    return {
        'service': service, 'booking_id': booking_id, 'reference': str(reference),
        'status': status, 'customer': customer, 'booking_date': booking_date,
        'amount': dict(details).get('Amount', ''), 'details': details,
        'people': people,
    }


def _first_name(people, user):
    if people:
        return people[0].get('full_name') or people[0].get('name') or 'Customer'
    return (user.get_full_name() or user.get_username()) if user else 'Customer'


def _person_line(person, index, label):
    bits = [f"{label} {index}: {person.get('full_name') or person.get('name') or 'Name not provided'}"]
    for key, title in (('age', 'Age'), ('gender', 'Gender'), ('email', 'Email'), ('phone_number', 'Phone')):
        if person.get(key):
            bits.append(f'{title}: {person[key]}')
    if person.get('seat_number'):
        bits.append(f"Seat/Berth: {person['seat_number']}")
    return ' · '.join(str(bit) for bit in bits)


def _reserved_or_passenger_seats(booking, passengers, service_key):
    seats = [p.get('seat_number') for p in passengers if p.get('seat_number')]
    if not seats:
        try:
            seats = list(booking.reserved_seats.values_list('seat_number', flat=True))
        except (AttributeError, TypeError):
            seats = []
    return seats


def _money(amount):
    return f'₹{Decimal(amount):,.2f}'
