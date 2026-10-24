import secrets
import string
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from quadori.notifications import send_booking_confirmation, send_booking_sms
from mybookings.tickets import ticket_context

from .forms import CustomerDetailsForm, MovieSearchForm
from .models import MovieBooking, ReservedSeat


TICKET_PRICE = Decimal('220.00')
SHOW_TIMES = ('10:00 AM', '1:30 PM', '5:00 PM', '9:00 PM')
SEAT_NUMBERS = [f'{row}{letter}' for row in range(1, 11) for letter in 'ABCDEF']
MAX_TICKETS = 10

# Catalogue entries and theatre schedules are sample data; bookings and seats are persisted.
from .catalog import (
    GENRES, MOVIE_RELEASE_YEARS, MOVIE_TITLES, get_poster_url,
    placeholder_poster_url,
)


THEATRES_BY_CITY = {
    'Chennai': (
        ('sathyam-chennai', 'Sathyam Cinemas', 'Sathyam'),
        ('ags-t-nagar-chennai', 'AGS T. Nagar', 'AGS'),
        ('pvr-ampasky-chennai', 'PVR Ampa Skywalk', 'PVR'),
        ('inox-chennai', 'INOX Chennai Citi Centre', 'INOX'),
    ),
    'Hyderabad': (
        ('prasads-hyderabad', 'Prasads Multiplex', 'PVR'),
        ('inox-gvk-hyderabad', 'INOX GVK One', 'INOX'),
        ('cinepolis-hyderabad', 'Cinepolis Manjeera', 'Cinepolis'),
    ),
    'Bengaluru': (
        ('pvr-orion-bengaluru', 'PVR Orion Mall', 'PVR'),
        ('inox-garuda-bengaluru', 'INOX Garuda Mall', 'INOX'),
        ('cinepolis-bengaluru', 'Cinepolis Royal Meenakshi', 'Cinepolis'),
    ),
    'Mumbai': (
        ('pvr-icon-mumbai', 'PVR ICON, Infiniti Mall', 'PVR'),
        ('inox-nariman-mumbai', 'INOX Nariman Point', 'INOX'),
        ('cinepolis-mumbai', 'Cinepolis Andheri', 'Cinepolis'),
    ),
    'Delhi': (
        ('pvr-select-city-delhi', 'PVR Select Citywalk', 'PVR'),
        ('inox-delhi', 'INOX Nehru Place', 'INOX'),
        ('cinepolis-janakpuri-delhi', 'Cinepolis Janakpuri', 'Cinepolis'),
    ),
    'Kochi': (
        ('pvr-lulu-kochi', 'PVR Lulu Mall', 'PVR'),
        ('inox-kochi', 'INOX Centre Square', 'INOX'),
        ('cinepolis-centre-kochi', 'Cinepolis Centre Square', 'Cinepolis'),
    ),
    'Kolkata': (
        ('inox-south-city-kolkata', 'INOX South City', 'INOX'),
        ('cinepolis-kolkata', 'Cinepolis Acropolis', 'Cinepolis'),
        ('pvr-kolkata', 'PVR Diamond Plaza', 'PVR'),
    ),
    'Jaipur': (
        ('pvr-world-trade-jaipur', 'PVR World Trade Park', 'PVR'),
        ('inox-crystal-jaipur', 'INOX Crystal Palm', 'INOX'),
        ('cinepolis-jaipur', 'Cinepolis Triton Mall', 'Cinepolis'),
    ),
    'Pune': (
        ('pvr-pavilion-pune', 'PVR Pavilion Mall', 'PVR'),
        ('inox-pune', 'INOX Bund Garden', 'INOX'),
        ('cinepolis-westend-pune', 'Cinepolis Westend Mall', 'Cinepolis'),
    ),
    'Ahmedabad': (
        ('cinepolis-alpha-ahmedabad', 'Cinepolis Alpha One', 'Cinepolis'),
        ('pvr-acropolis-ahmedabad', 'PVR Acropolis Mall', 'PVR'),
        ('inox-ahmedabad', 'INOX Himalaya Mall', 'INOX'),
    ),
}

SAMPLE_MOVIES = []
_ENGLISH_CITIES = ('Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Kolkata', 'Jaipur', 'Pune', 'Ahmedabad', 'Kochi')
_DURATION_SAMPLES = ('1h 52m', '2h 05m', '2h 14m', '2h 21m', '2h 32m', '2h 44m')
for _language, _titles in MOVIE_TITLES.items():
    for _index, _title in enumerate(_titles):
        if _language == 'Tamil':
            _city = 'Chennai'
        elif _language == 'Telugu':
            _city = 'Hyderabad'
        elif _language == 'Kannada':
            _city = 'Bengaluru'
        elif _language == 'Malayalam':
            _city = 'Kochi'
        elif _language == 'Hindi':
            _city = 'Mumbai' if _index < len(_titles) // 2 else 'Delhi'
        else:
            _city = _ENGLISH_CITIES[_index % len(_ENGLISH_CITIES)]
        _genres = GENRES[_language]
        _poster = placeholder_poster_url(_title)
        SAMPLE_MOVIES.append({
            'id': f'catalog-{_language.lower()}-{_index + 1:03d}',
            'name': _title,
            'city': _city,
            'language': _language,
            'release_year': MOVIE_RELEASE_YEARS[_title],
            'genre': _genres[_index % len(_genres)],
            'duration': _DURATION_SAMPLES[(_index * 3 + len(_language)) % len(_DURATION_SAMPLES)],
            'rating': f'{7.1 + ((_index * 7 + len(_language)) % 20) / 10:.1f}',
            'description': f'{_title} is a {_genres[_index % len(_genres)].lower()} film presented in {_language}.',
            'poster_url': _poster,
            'theatres': THEATRES_BY_CITY[_city],
        })



def _get_movie(movie_code):
    movie = next((movie for movie in SAMPLE_MOVIES if movie['id'] == movie_code), None)
    if movie is None:
        return None
    return {**movie, 'poster_url': get_poster_url(movie['name'], movie['release_year'], movie['language'])}


def _get_theatre(movie, theatre_code):
    return next((
        {'code': code, 'name': name, 'brand': brand}
        for code, name, brand in movie['theatres'] if code == theatre_code
    ), None)


def _seat_state(movie_code, theatre_code, show_date, show_time):
    return set(ReservedSeat.objects.filter(
        movie_code=movie_code, theatre_code=theatre_code,
        show_date=show_date, show_time=show_time,
    ).values_list('seat_number', flat=True))


@login_required(login_url='accounts:login')
def search_movies(request):
    form = MovieSearchForm(request.GET if request.GET else None)
    movies = []
    show_date = timezone.localdate() + timedelta(days=1)
    if not request.GET:
        for original in SAMPLE_MOVIES:
            movies.append({
                **original,
                'poster_url': get_poster_url(original['name'], original['release_year'], original['language']),
                'available_theatres': [
                    {'code': code, 'name': name, 'brand': brand}
                    for code, name, brand in original['theatres']
                ],
            })
    elif form.is_valid():
        cleaned = form.cleaned_data
        show_date = cleaned.get('show_date') or show_date
        for original in SAMPLE_MOVIES:
            if cleaned.get('city') and original['city'] != cleaned['city']:
                continue
            theatres = [
                {'code': code, 'name': name, 'brand': brand}
                for code, name, brand in original['theatres']
                if not cleaned.get('theatre') or brand == cleaned['theatre']
            ]
            if theatres:
                movie = {**original, 'poster_url': get_poster_url(original['name'], original['release_year'], original['language']), 'available_theatres': theatres}
                movies.append(movie)
    return render(request, 'movie/search.html', {
        'form': form, 'movies': movies, 'show_date': show_date,
        'show_times': SHOW_TIMES, 'ticket_price': TICKET_PRICE,
    })


@login_required(login_url='accounts:login')
def book_movie(request):
    get_value = request.POST.get if request.method == 'POST' else request.GET.get
    movie = _get_movie(get_value('movie_code', ''))
    if movie is None:
        raise Http404('Movie not found.')
    theatre = _get_theatre(movie, get_value('theatre_code', ''))
    if theatre is None:
        raise Http404('Theatre not found for this movie.')
    show_time = get_value('show_time', '')
    if show_time not in SHOW_TIMES:
        raise Http404('Show time not found.')
    try:
        from django.utils.dateparse import parse_date
        show_date = parse_date(get_value('show_date', ''))
    except (TypeError, ValueError):
        show_date = None
    if show_date is None:
        show_date = timezone.localdate() + timedelta(days=1)
    if show_date < timezone.localdate():
        raise Http404('Show date cannot be in the past.')

    booked_seats = _seat_state(movie['id'], theatre['code'], show_date, show_time)
    selected_seats = request.POST.getlist('seats') if request.method == 'POST' else []
    form = CustomerDetailsForm(request.POST or None, initial={
        'customer_name': request.user.get_full_name() or request.user.username,
        'customer_email': request.user.email,
    })
    seat_error = ''

    if request.method == 'POST' and form.is_valid():
        if not selected_seats or len(selected_seats) > MAX_TICKETS:
            seat_error = f'Choose between 1 and {MAX_TICKETS} seats.'
        elif len(set(selected_seats)) != len(selected_seats) or any(seat not in SEAT_NUMBERS for seat in selected_seats):
            seat_error = 'One or more selected seats are invalid.'
        elif any(seat in booked_seats for seat in selected_seats):
            seat_error = 'A selected seat is no longer available. Please choose again.'
        else:
            try:
                with transaction.atomic():
                    booking = MovieBooking.objects.create(
                        user=request.user,
                        movie_code=movie['id'], movie_name=movie['name'],
                        movie_description=movie['description'], poster_url=movie['poster_url'],
                        language=movie['language'], genre=movie['genre'], duration=movie['duration'],
                        rating=movie['rating'], city=movie['city'],
                        theatre_code=theatre['code'], theatre_name=theatre['name'],
                        show_date=show_date, show_time=show_time,
                        ticket_price=TICKET_PRICE, seat_count=len(selected_seats),
                        seat_numbers=selected_seats,
                        customer_name=form.cleaned_data['customer_name'],
                        customer_phone=form.cleaned_data['customer_phone'],
                        customer_email=form.cleaned_data['customer_email'],
                        total_amount=TICKET_PRICE * len(selected_seats),
                    )
                    ReservedSeat.objects.bulk_create([
                        ReservedSeat(
                            booking=booking, movie_code=movie['id'],
                            theatre_code=theatre['code'], show_date=show_date,
                            show_time=show_time, seat_number=seat,
                        ) for seat in selected_seats
                    ])
                send_booking_confirmation(
                    recipient=booking.customer_email,
                    customer_name=booking.customer_name,
                    booking_id=booking.booking_id,
                    reference=booking.booking_number,
                    service_name='Movie Booking',
                    booking_date=booking.show_date.strftime('%d %b %Y'),
                    booking_time=booking.show_time,
                    amount=booking.total_amount,
                )
                send_booking_sms(
                    recipient=booking.customer_phone,
                    customer_name=booking.customer_name,
                    booking_id=booking.booking_id,
                    reference=booking.booking_number,
                    service_name='Movie Booking',
                    booking_date=booking.show_date.strftime('%d %b %Y'),
                    booking_time=booking.show_time,
                    amount=booking.total_amount,
                )
                return redirect('movie:confirmation', booking_id=booking.booking_id)
            except IntegrityError:
                seat_error = 'A selected seat was just booked. Please choose available seats.'
                booked_seats = _seat_state(movie['id'], theatre['code'], show_date, show_time)

    seat_layout = [{
        'number': seat, 'reserved': seat in booked_seats,
        'selected': seat in selected_seats and seat not in booked_seats,
    } for seat in SEAT_NUMBERS]
    return render(request, 'movie/booking.html', {
        'form': form, 'movie': movie, 'theatre': theatre,
        'show_date': show_date, 'show_time': show_time,
        'seat_layout': seat_layout, 'selected_seats': selected_seats,
        'seat_error': seat_error, 'max_tickets': MAX_TICKETS,
        'ticket_price': TICKET_PRICE,
        'total_amount': TICKET_PRICE * len([s for s in selected_seats if s not in booked_seats]),
    })


@login_required(login_url='accounts:login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        MovieBooking.objects.prefetch_related('reserved_seats'),
        booking_id=booking_id, user=request.user,
    )
    return render(request, 'movie/confirmation.html', {
        'booking': booking, **ticket_context('movie', booking),
    })
