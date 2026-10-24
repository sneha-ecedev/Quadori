from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from quadori.notifications import send_booking_confirmation, send_booking_sms
from quadori.city_data import INDIAN_CITY_NAMES
from mybookings.tickets import ticket_context

from .forms import CustomerDetailsForm, RestaurantSearchForm
from .models import RestaurantBooking


SAMPLE_RESTAURANTS = [
    {
        'id': 'saravana-delhi', 'name': 'Saravana Bhavan', 'city': 'Delhi',
        'address': 'Janpath, Connaught Place, New Delhi', 'rating': Decimal('4.5'),
        'cuisine': 'South Indian', 'opening_hours': '08:00 AM – 10:30 PM',
        'average_cost': Decimal('650.00'),
        'image_url': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'punjab-mumbai', 'name': 'Punjab Grill', 'city': 'Mumbai',
        'address': 'Phoenix Palladium, Lower Parel, Mumbai', 'rating': Decimal('4.6'),
        'cuisine': 'North Indian', 'opening_hours': '12:00 PM – 11:00 PM',
        'average_cost': Decimal('1800.00'),
        'image_url': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'mamagoto-bengaluru', 'name': 'Mamagoto', 'city': 'Bengaluru',
        'address': 'Indiranagar 100 Feet Road, Bengaluru', 'rating': Decimal('4.3'),
        'cuisine': 'Chinese', 'opening_hours': '12:00 PM – 11:00 PM',
        'average_cost': Decimal('1400.00'),
        'image_url': 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'little-italy-jaipur', 'name': 'Little Italy', 'city': 'Jaipur',
        'address': 'C Scheme, Ashok Nagar, Jaipur', 'rating': Decimal('4.4'),
        'cuisine': 'Italian', 'opening_hours': '12:30 PM – 10:45 PM',
        'average_cost': Decimal('1600.00'),
        'image_url': 'https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'coast-cafe-goa', 'name': 'Coast Café', 'city': 'Goa',
        'address': 'Candolim Beach Road, North Goa', 'rating': Decimal('4.2'),
        'cuisine': 'Fast Food', 'opening_hours': '09:00 AM – 11:00 PM',
        'average_cost': Decimal('900.00'),
        'image_url': 'https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'malabar-kochi', 'name': 'Malabar Kitchen', 'city': 'Kochi',
        'address': 'Fort Kochi Beach Road, Kochi', 'rating': Decimal('4.5'),
        'cuisine': 'South Indian', 'opening_hours': '11:30 AM – 10:30 PM',
        'average_cost': Decimal('850.00'),
        'image_url': 'https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'thali-udaipur', 'name': 'The Royal Thali House', 'city': 'Udaipur',
        'address': 'City Palace Road, Udaipur', 'rating': Decimal('4.7'),
        'cuisine': 'North Indian', 'opening_hours': '11:00 AM – 10:00 PM',
        'average_cost': Decimal('1100.00'),
        'image_url': 'https://images.unsplash.com/photo-1515003197210-e0cd7184f8b5?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'noodle-house-hyderabad', 'name': 'Noodle House', 'city': 'Hyderabad',
        'address': 'Jubilee Hills Road No. 36, Hyderabad', 'rating': Decimal('4.1'),
        'cuisine': 'Chinese', 'opening_hours': '12:00 PM – 11:30 PM',
        'average_cost': Decimal('1200.00'),
        'image_url': 'https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'marina-chen', 'name': 'Marina Diner', 'city': 'Chennai',
        'address': 'Santhome High Road, Chennai', 'rating': Decimal('4.0'),
        'cuisine': 'Fast Food', 'opening_hours': '10:00 AM – 11:00 PM',
        'average_cost': Decimal('750.00'),
        'image_url': 'https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=1200&q=85',
    },
    {
        'id': 'peshawri-agra', 'name': 'Peshawri Table', 'city': 'Agra',
        'address': 'Fatehabad Road, Agra, Uttar Pradesh', 'rating': Decimal('4.6'),
        'cuisine': 'North Indian', 'opening_hours': '12:00 PM – 10:45 PM',
        'average_cost': Decimal('2000.00'),
        'image_url': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=85',
    },
]

_sample_cuisines = ('South Indian', 'North Indian', 'Chinese', 'Italian', 'Fast Food')
for _city_index, _city in enumerate(INDIAN_CITY_NAMES, start=1):
    for _cuisine_index, _cuisine in enumerate(_sample_cuisines, start=1):
        SAMPLE_RESTAURANTS.append({
            'id': f'quadori-restaurant-{_city_index:02d}-{_cuisine_index}',
            'name': f'{_city} {_cuisine} Kitchen',
            'city': _city,
            'address': f'{_cuisine_index} Market Road, {_city}, India',
            'rating': Decimal(str(4 + ((_city_index + _cuisine_index) % 10) / 10)),
            'cuisine': _cuisine,
            'opening_hours': '08:00 AM – 11:00 PM',
            'average_cost': Decimal(str(500 + ((_city_index + _cuisine_index) % 12) * 125)),
            'image_url': (
                'https://images.unsplash.com/photo-1414235077428-338989a2e8c0'
                '?auto=format&fit=crop&w=1200&q=85'
            ),
        })


@login_required(login_url='accounts:login')
def search_restaurants(request):
    today = timezone.localdate()
    if request.GET:
        form = RestaurantSearchForm(request.GET)
        restaurants = []
        if form.is_valid():
            city = form.cleaned_data['city']
            cuisine = form.cleaned_data['cuisine']
            booking_date = form.cleaned_data['booking_date']
            booking_time = form.cleaned_data['booking_time']
            guests = form.cleaned_data['guests']
            restaurants = [
                restaurant for restaurant in SAMPLE_RESTAURANTS
                if restaurant['city'] == city
                and (not cuisine or restaurant['cuisine'] == cuisine)
            ]
        else:
            booking_date = None
            booking_time = None
            guests = 2
    else:
        booking_date = today + timedelta(days=1)
        booking_time = time(19, 0)
        guests = 2
        form = RestaurantSearchForm(initial={
            'booking_date': booking_date,
            'booking_time': booking_time,
            'guests': guests,
        })
        restaurants = SAMPLE_RESTAURANTS[:10]

    return render(request, 'restaurant/search.html', {
        'form': form,
        'restaurants': restaurants,
        'booking_date': booking_date,
        'booking_time': booking_time,
        'guests': guests,
    })


@login_required(login_url='accounts:login')
def reserve_table(request):
    restaurant_id = request.POST.get('restaurant_id') if request.method == 'POST' else request.GET.get('restaurant_id')
    restaurant = next(
        (item for item in SAMPLE_RESTAURANTS if item['id'] == restaurant_id),
        None,
    )
    if restaurant is None:
        raise Http404('Restaurant not found.')

    get_value = request.POST.get if request.method == 'POST' else request.GET.get
    booking_date = parse_date(get_value('booking_date', '') or '')
    booking_time = parse_time(get_value('booking_time', '') or '')
    try:
        guests = int(get_value('guests', ''))
    except (TypeError, ValueError):
        raise Http404('Invalid guest count.')

    now = timezone.localtime()
    if (
        booking_date is None
        or booking_time is None
        or booking_date < timezone.localdate()
        or not 1 <= guests <= 20
        or (
            booking_date == timezone.localdate()
            and booking_time <= now.time().replace(second=0, microsecond=0)
        )
    ):
        raise Http404('Invalid reservation details.')

    form = CustomerDetailsForm(request.POST or None, initial={
        'customer_name': request.user.get_full_name() or request.user.username,
    })
    if request.method == 'POST' and form.is_valid():
        booking = RestaurantBooking.objects.create(
            user=request.user,
            restaurant_code=restaurant['id'],
            restaurant_name=restaurant['name'],
            address=restaurant['address'],
            city=restaurant['city'],
            cuisine=restaurant['cuisine'],
            opening_hours=restaurant['opening_hours'],
            average_cost=restaurant['average_cost'],
            booking_date=booking_date,
            booking_time=booking_time,
            guest_count=guests,
            customer_name=form.cleaned_data['customer_name'],
            customer_phone=form.cleaned_data['customer_phone'],
            customer_email=form.cleaned_data['customer_email'],
        )
        send_booking_confirmation(
            recipient=booking.customer_email,
            customer_name=booking.customer_name,
            booking_id=booking.booking_id,
            reference=f'RST-{booking.booking_id.hex[:10].upper()}',
            service_name='Restaurant Booking',
            booking_date=booking.booking_date.strftime('%d %b %Y'),
            booking_time=booking.booking_time.strftime('%I:%M %p'),
            amount=booking.average_cost * booking.guest_count,
        )
        send_booking_sms(
            recipient=booking.customer_phone,
            customer_name=booking.customer_name,
            booking_id=booking.booking_id,
            reference=f'RST-{booking.booking_id.hex[:10].upper()}',
            service_name='Restaurant Booking',
            booking_date=booking.booking_date.strftime('%d %b %Y'),
            booking_time=booking.booking_time.strftime('%I:%M %p'),
            amount=booking.average_cost * booking.guest_count,
        )
        return redirect('restaurant:confirmation', booking_id=booking.booking_id)

    return render(request, 'restaurant/customer_details.html', {
        'restaurant': restaurant,
        'booking_date': booking_date,
        'booking_time': booking_time,
        'guests': guests,
        'form': form,
    })


@login_required(login_url='accounts:login')
def booking_confirmation(request, booking_id):
    booking = get_object_or_404(
        RestaurantBooking,
        booking_id=booking_id,
        user=request.user,
    )
    return render(request, 'restaurant/confirmation.html', {
        'booking': booking, **ticket_context('restaurant', booking),
    })
