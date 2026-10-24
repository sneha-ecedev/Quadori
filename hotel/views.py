from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from quadori.notifications import send_booking_confirmation, send_booking_sms
from quadori.city_data import INDIAN_CITY_NAMES
from mybookings.tickets import ticket_context

from .forms import GuestForm, HotelSearchForm
from .models import HotelBooking


ROOM_MULTIPLIERS = {
    'Standard': Decimal('1.00'),
    'Deluxe': Decimal('1.45'),
    'Suite': Decimal('2.10'),
}

SAMPLE_HOTELS = [
    {
        'id': 'imperial-delhi', 'name': 'The Imperial New Delhi',
        'city': 'Delhi', 'address': 'Janpath, Connaught Place, New Delhi',
        'rating': 5, 'base_price': Decimal('12500.00'),
        'image_url': 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'marine-mumbai', 'name': 'Marine Bay Hotel',
        'city': 'Mumbai', 'address': 'Marine Drive, Churchgate, Mumbai',
        'rating': 4, 'base_price': Decimal('8200.00'),
        'image_url': 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'garden-bengaluru', 'name': 'Garden City Suites',
        'city': 'Bengaluru', 'address': 'Residency Road, Bengaluru',
        'rating': 4, 'base_price': Decimal('6900.00'),
        'image_url': 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'pink-jaipur', 'name': 'Pink City Heritage Haveli',
        'city': 'Jaipur', 'address': 'Amer Road, Jaipur, Rajasthan',
        'rating': 4, 'base_price': Decimal('5600.00'),
        'image_url': 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'coconut-goa', 'name': 'Coconut Grove Resort',
        'city': 'Goa', 'address': 'Candolim Beach Road, North Goa',
        'rating': 5, 'base_price': Decimal('9800.00'),
        'image_url': 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'backwater-kochi', 'name': 'Backwater Pearl Hotel',
        'city': 'Kochi', 'address': 'Marine Drive, Ernakulam, Kochi',
        'rating': 4, 'base_price': Decimal('6100.00'),
        'image_url': 'https://images.unsplash.com/photo-1564501049412-61c2a3083791?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'lake-udaipur', 'name': 'Lake Palace View Retreat',
        'city': 'Udaipur', 'address': 'Lake Pichola Road, Udaipur',
        'rating': 5, 'base_price': Decimal('11200.00'),
        'image_url': 'https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'charminar-hyderabad', 'name': 'Deccan Grand Hyderabad',
        'city': 'Hyderabad', 'address': 'Banjara Hills, Hyderabad',
        'rating': 4, 'base_price': Decimal('6400.00'),
        'image_url': 'https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'marina-chennai', 'name': 'Marina Bay Residency',
        'city': 'Chennai', 'address': 'Kamarajar Salai, Chennai',
        'rating': 4, 'base_price': Decimal('7200.00'),
        'image_url': 'https://images.unsplash.com/photo-1568084680786-a84f91d1153c?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'taj-agra', 'name': 'Taj Garden View Agra',
        'city': 'Agra', 'address': 'Fatehabad Road, Agra, Uttar Pradesh',
        'rating': 5, 'base_price': Decimal('8900.00'),
        'image_url': 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=1200&q=85',
    },
]

# Provide multiple choices in every supported city, including cities added later.
for _city_index, _city in enumerate(INDIAN_CITY_NAMES, start=1):
    for _option in range(1, 3):
        SAMPLE_HOTELS.append({
            'id': f'quadori-hotel-{_city_index:02d}-{_option}',
            'name': f'{_city} {_option} {"Grand Hotel" if _option == 1 else "City Stay"}',
            'city': _city,
            'address': f'{_option} Central Avenue, {_city}, India',
            'rating': 4 if _option == 1 else 3,
            'base_price': Decimal(str(2800 + ((_city_index * 2 + _option) % 18) * 450)),
            'image_url': (
                'https://images.unsplash.com/photo-1566073771259-6a8506099945'
                '?auto=format&fit=crop&w=1200&q=85'
            ),
        })


def _price_per_room_night(hotel, room_type):
    return hotel['base_price'] * ROOM_MULTIPLIERS[room_type]


@login_required(login_url='accounts:login')
def search_hotels(request):
    today = timezone.localdate()
    if request.GET:
        form = HotelSearchForm(request.GET)
        hotels = []
        if form.is_valid():
            city = form.cleaned_data['city']
            check_in = form.cleaned_data['check_in']
            check_out = form.cleaned_data['check_out']
            adults = form.cleaned_data['adults']
            children = form.cleaned_data['children']
            guests = adults + children
            rooms = form.cleaned_data['rooms']
            hotels = [hotel for hotel in SAMPLE_HOTELS if hotel['city'] == city]
        else:
            check_in = None
            check_out = None
            adults = 2
            children = 0
            guests = 2
            rooms = 1
    else:
        check_in = today
        check_out = today + timedelta(days=1)
        adults = 2
        children = 0
        guests = 2
        rooms = 1
        form = HotelSearchForm(initial={
            'check_in': check_in,
            'check_out': check_out,
            'adults': adults,
            'children': children,
            'rooms': rooms,
        })
        hotels = SAMPLE_HOTELS

    if check_in and check_out:
        nights = (check_out - check_in).days
        for hotel in hotels:
            hotel['nights'] = nights
            hotel['room_prices'] = {
                room_type: _price_per_room_night(hotel, room_type)
                for room_type in ROOM_MULTIPLIERS
            }
    else:
        nights = None

    return render(request, 'hotel/search.html', {
        'form': form,
        'hotels': hotels,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'guests': guests,
        'adults': adults,
        'children': children,
        'rooms': rooms,
        'room_types': ROOM_MULTIPLIERS,
    })


@login_required(login_url='accounts:login')
def book_hotel(request):
    hotel_id = request.POST.get('hotel_id') if request.method == 'POST' else request.GET.get('hotel_id')
    hotel = next((item for item in SAMPLE_HOTELS if item['id'] == hotel_id), None)
    if hotel is None:
        raise Http404('Hotel not found.')

    get_value = request.POST.get if request.method == 'POST' else request.GET.get
    check_in = parse_date(get_value('check_in', '') or '')
    check_out = parse_date(get_value('check_out', '') or '')
    room_type = get_value('room_type', '')
    try:
        adults = int(get_value('adults', ''))
        children = int(get_value('children', ''))
        rooms = int(get_value('rooms', ''))
    except (TypeError, ValueError):
        raise Http404('Invalid guest or room count.')

    if (
        check_in is None
        or check_out is None
        or check_in < timezone.localdate()
        or check_out <= check_in
        or room_type not in ROOM_MULTIPLIERS
        or not 1 <= adults <= 8
        or not 0 <= children <= 8
        or adults + children > 8
        or not 1 <= rooms <= 5
    ):
        raise Http404('Invalid stay details.')

    nights = (check_out - check_in).days
    guests = adults + children
    nightly_rate = _price_per_room_night(hotel, room_type)
    total_price = nightly_rate * nights * rooms
    GuestFormSet = formset_factory(
        GuestForm,
        extra=0,
        min_num=guests,
        max_num=guests,
        validate_min=True,
        validate_max=True,
    )
    formset = GuestFormSet(request.POST or None)

    if request.method == 'POST' and formset.is_valid():
        booking = HotelBooking.objects.create(
            user=request.user,
            hotel_code=hotel['id'],
            hotel_name=hotel['name'],
            image_url=hotel['image_url'],
            address=hotel['address'],
            city=hotel['city'],
            check_in=check_in,
            check_out=check_out,
            nights=nights,
            guest_count=guests,
            adult_count=adults,
            child_count=children,
            room_count=rooms,
            room_type=room_type,
            guest_details=[form.cleaned_data for form in formset],
            price_per_room_night=nightly_rate,
            total_price=total_price,
        )
        primary_guest = booking.guest_details[0]
        send_booking_confirmation(
            recipient=primary_guest['email'],
            customer_name=primary_guest['full_name'],
            booking_id=booking.booking_id,
            reference=f'HTL-{booking.booking_id.hex[:10].upper()}',
            service_name='Hotel Booking',
            booking_date=(
                f'{booking.check_in:%d %b %Y} to {booking.check_out:%d %b %Y}'
            ),
            booking_time='Check-in time to be confirmed with the hotel',
            amount=booking.total_price,
        )
        send_booking_sms(
            recipient=primary_guest['phone_number'],
            customer_name=primary_guest['full_name'],
            booking_id=booking.booking_id,
            reference=f'HTL-{booking.booking_id.hex[:10].upper()}',
            service_name='Hotel Booking',
            booking_date=(
                f'{booking.check_in:%d %b %Y} to {booking.check_out:%d %b %Y}'
            ),
            booking_time='Check-in time to be confirmed with the hotel',
            amount=booking.total_price,
        )
        return redirect('hotel:confirmation', booking_id=booking.booking_id)

    return render(request, 'hotel/guest_details.html', {
        'hotel': hotel,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'guests': guests,
        'adults': adults,
        'children': children,
        'rooms': rooms,
        'room_type': room_type,
        'nightly_rate': nightly_rate,
        'total_price': total_price,
        'formset': formset,
    })


@login_required(login_url='accounts:login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        HotelBooking,
        booking_id=booking_id,
        user=request.user,
    )
    return render(request, 'hotel/confirmation.html', {
        'booking': booking, **ticket_context('hotel', booking),
    })
