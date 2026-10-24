from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from bus.models import BusBooking
from flight.models import Booking as FlightBooking
from hotel.models import HotelBooking
from movie.models import MovieBooking
from restaurant.models import RestaurantBooking
from train.models import TrainBooking
from bus.models import ReservedSeat as BusReservedSeat
from train.models import ReservedSeat as TrainReservedSeat
from movie.models import ReservedSeat as MovieReservedSeat
from quadori.notifications import send_booking_cancellation_email, send_booking_cancellation_sms
from .tickets import TICKET_SOURCES, build_ticket_pdf

from .forms import BookingFilterForm


BOOKING_SOURCES = {
    'flight': (FlightBooking, 'Flight', 'flight:confirmation'),
    'bus': (BusBooking, 'Bus', 'bus:confirmation'),
    'train': (TrainBooking, 'Train', 'train:confirmation'),
    'hotel': (HotelBooking, 'Hotel', 'hotel:confirmation'),
    'restaurant': (RestaurantBooking, 'Restaurant', 'restaurant:confirmation'),
    'movie': (MovieBooking, 'Movie', 'movie:confirmation'),
}


@login_required(login_url='accounts:login')
def booking_list(request):
    form = BookingFilterForm(request.GET)
    bookings = []

    if form.is_valid():
        selected_service = form.cleaned_data['service_type']
        id_search = form.cleaned_data['booking_id'].strip().lower()
        service_keys = [selected_service] if selected_service else BOOKING_SOURCES.keys()

        for service_key in service_keys:
            model, service_name, detail_url_name = BOOKING_SOURCES[service_key]
            booking_query = model.objects.filter(user=request.user).order_by('-created_at')
            if service_key in ('bus', 'train'):
                booking_query = booking_query.prefetch_related('reserved_seats')
            for booking in booking_query:
                booking_id = str(booking.booking_id)
                if id_search and id_search not in booking_id.lower():
                    continue
                bookings.append({
                    'booking_id': booking_id,
                    'booking_date': booking.created_at,
                    'service_type': service_name,
                    'status': booking.get_status_display(),
                    'is_confirmed': booking.status == 'confirmed',
                    'cancel_url': reverse('mybookings:cancel', kwargs={
                        'service_key': service_key, 'booking_id': booking.booking_id,
                    }),
                    'ticket_url': reverse('mybookings:ticket', kwargs={
                        'service_key': service_key, 'booking_id': booking.booking_id,
                    }),
                    'party_summary': _party_summary(service_key, booking),
                    'detail_url': reverse(
                        detail_url_name,
                        kwargs={'booking_id': booking.booking_id},
                    ),
                })

    bookings.sort(key=lambda item: item['booking_date'], reverse=True)
    return render(request, 'mybookings/list.html', {
        'form': form,
        'bookings': bookings,
    })


@login_required(login_url='accounts:login')
def cancel_booking(request, service_key, booking_id):
    if request.method != 'POST':
        return redirect('mybookings:list')
    source = BOOKING_SOURCES.get(service_key)
    if source is None:
        messages.error(request, 'That booking type is not available.')
        return redirect('mybookings:list')
    model = source[0]
    with transaction.atomic():
        booking = get_object_or_404(
            model.objects.select_for_update(), booking_id=booking_id, user=request.user,
        )
        if booking.status != 'confirmed':
            messages.info(request, 'This booking has already been cancelled.')
            return redirect('mybookings:list')
        if service_key == 'movie' and not booking.seat_numbers:
            booking.seat_numbers = list(
                MovieReservedSeat.objects.filter(booking=booking)
                .values_list('seat_number', flat=True)
            )
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        update_fields = ['status', 'cancelled_at']
        if service_key == 'movie':
            update_fields.append('seat_numbers')
        booking.save(update_fields=update_fields)
        if service_key == 'bus':
            BusReservedSeat.objects.filter(booking=booking).delete()
        elif service_key == 'train':
            TrainReservedSeat.objects.filter(booking=booking).delete()
        elif service_key == 'movie':
            MovieReservedSeat.objects.filter(booking=booking).delete()

    name, email, phone = _cancellation_contact(service_key, booking)
    booking_date, booking_time = _booking_datetime(service_key, booking)
    notification = {
        'recipient': email, 'customer_name': name, 'booking_id': booking.booking_id,
        'reference': _booking_reference(service_key, booking),
        'service_name': f'{source[1]} Booking', 'booking_date': booking_date,
        'booking_time': booking_time, 'amount': _booking_amount(service_key, booking),
    }
    send_booking_cancellation_email(**notification)
    send_booking_cancellation_sms(**{**notification, 'recipient': phone})
    messages.success(request, 'Your booking was cancelled. Any reserved seats have been released.')
    return redirect('mybookings:list')


@login_required(login_url='accounts:login')
def download_ticket(request, service_key, booking_id):
    source = TICKET_SOURCES.get(service_key)
    if source is None:
        return redirect('mybookings:list')
    booking = get_object_or_404(
        source[0].objects.filter(user=request.user), booking_id=booking_id,
    )
    pdf = build_ticket_pdf(service_key, booking)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="quadori-{service_key}-ticket-{booking.booking_id}.pdf"'
    return response


def _cancellation_contact(service_key, booking):
    if service_key in ('flight', 'bus', 'train'):
        passenger = (booking.passenger_details or [{}])[0]
        user = booking.user
        return (passenger.get('full_name') or user.get_full_name() or user.get_username(),
                passenger.get('email') or user.email, passenger.get('phone_number', ''))
    if service_key == 'hotel':
        guest = (booking.guest_details or [{}])[0]
        return guest.get('full_name', ''), guest.get('email') or booking.user.email, guest.get('phone_number', '')
    return booking.customer_name, booking.customer_email or booking.user.email, booking.customer_phone


def _booking_reference(service_key, booking):
    if service_key in ('flight', 'train'):
        return booking.pnr_number
    if service_key == 'movie':
        return booking.booking_number
    prefix = {'bus': 'BUS', 'hotel': 'HTL', 'restaurant': 'RST'}[service_key]
    return f'{prefix}-{booking.booking_id.hex[:10].upper()}'


def _booking_datetime(service_key, booking):
    fields = {
        'flight': ('flight_date', 'departure_time'),
        'bus': ('journey_date', 'departure_time'),
        'train': ('journey_date', 'departure_time'),
        'hotel': ('check_in', None),
        'restaurant': ('booking_date', 'booking_time'),
        'movie': ('show_date', 'show_time'),
    }
    date_field, time_field = fields[service_key]
    booking_date = getattr(booking, date_field, None)
    if time_field is None:
        booking_time = 'Check-in time to be confirmed'
    else:
        booking_time = getattr(booking, time_field, None)
        if service_key == 'restaurant' and booking_time is not None:
            booking_time = booking_time.strftime('%I:%M %p')
    return booking_date, booking_time or 'Time not specified'


def _booking_amount(service_key, booking):
    if service_key == 'restaurant':
        return booking.average_cost * booking.guest_count
    if service_key in ('flight', 'hotel'):
        return booking.total_price
    if service_key in ('bus', 'train'):
        return booking.total_fare
    return booking.total_amount


def _party_summary(service_key, booking):
    if service_key == 'flight':
        count = booking.passenger_count
        names = ', '.join(
            passenger.get('full_name', '').strip()
            for passenger in booking.passenger_details
            if passenger.get('full_name', '').strip()
        )
        return f"{count} passenger{'s' if count != 1 else ''}" + (f': {names}' if names else '')

    if service_key in ('bus', 'train'):
        passengers = booking.passenger_details or []
        count = booking.seat_count if service_key == 'bus' else booking.passenger_count
        seats = [seat.seat_number for seat in booking.reserved_seats.all()]
        assigned = [
            f"{passenger.get('full_name', '').strip()} ({passenger['seat_number']})"
            for passenger in passengers
            if passenger.get('full_name', '').strip() and passenger.get('seat_number')
        ]
        names = ', '.join(
            passenger.get('full_name', '').strip()
            for passenger in passengers
            if passenger.get('full_name', '').strip()
        )
        label = 'berth' if service_key == 'train' else 'seat'
        passenger_label = f"{count} passenger{'s' if count != 1 else ''}"
        summary_names = ', '.join(assigned) if assigned else names
        summary = f"{passenger_label}" + (f': {summary_names}' if summary_names else '')
        if seats:
            summary += f" \u00b7 {label}{'s' if len(seats) != 1 else ''}: " + ', '.join(seats)
        return summary

    if service_key == 'hotel':
        return (
            f'{booking.room_count} room' + ('s' if booking.room_count != 1 else '')
            + f' \u00b7 {booking.adult_count} adult' + ('s' if booking.adult_count != 1 else '')
            + f' \u00b7 {booking.child_count} child' + ('ren' if booking.child_count != 1 else '')
        )
    if service_key == 'restaurant':
        return f'{booking.guest_count} guest' + ('s' if booking.guest_count != 1 else '')
    if service_key == 'movie':
        seats = ', '.join(booking.seat_numbers or [])
        return f'{booking.seat_count} seat' + ('s' if booking.seat_count != 1 else '') + (f': {seats}' if seats else '')
    return ''
