from calendar import month_name
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.shortcuts import render
from django.utils import timezone

from bus.models import BusBooking
from flight.models import Booking as FlightBooking
from hotel.models import HotelBooking
from movie.models import MovieBooking
from restaurant.models import RestaurantBooking
from train.models import TrainBooking


REVENUE_FIELD = {
    'Flights': 'total_price',
    'Buses': 'total_fare',
    'Trains': 'total_fare',
    'Hotels': 'total_price',
    'Movies': 'total_amount',
}
SERVICES = (
    ('Flights', FlightBooking),
    ('Buses', BusBooking),
    ('Trains', TrainBooking),
    ('Hotels', HotelBooking),
    ('Restaurants', RestaurantBooking),
    ('Movies', MovieBooking),
)
PERIODS = ('today', 'week', 'month')


def _restaurant_amount_expression():
    return ExpressionWrapper(
        F('average_cost') * F('guest_count'),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


def _amount_expression(service):
    if service == 'Restaurants':
        return _restaurant_amount_expression()
    return F(REVENUE_FIELD[service])


def _period_bounds(period, today):
    if period == 'today':
        return today, today
    if period == 'week':
        return today - timedelta(days=today.weekday()), today
    if period == 'month':
        return today.replace(day=1), today
    return None, None


def _apply_date_range(queryset, start, end):
    if start:
        queryset = queryset.filter(created_at__date__gte=start)
    if end:
        queryset = queryset.filter(created_at__date__lte=end)
    return queryset


def _month_starts(current_month, count=12):
    index = current_month.year * 12 + current_month.month - 1
    starts = []
    for offset in reversed(range(count)):
        year, month_index = divmod(index - offset, 12)
        starts.append(current_month.replace(year=year, month=month_index + 1, day=1))
    return starts


@user_passes_test(
    lambda user: user.is_authenticated and user.is_staff,
    login_url='accounts:login',
)
def dashboard(request):
    today = timezone.localdate()
    period = request.GET.get('period', '').strip().lower()
    if period not in PERIODS:
        period = ''
    start_date, end_date = _period_bounds(period, today)
    search = request.GET.get('q', '').strip()[:100]

    base_querysets = {
        label: model.objects.all()
        for label, model in SERVICES
    }
    filtered_querysets = {
        label: _apply_date_range(queryset, start_date, end_date)
        for label, queryset in base_querysets.items()
    }

    counts = {
        label: queryset.count()
        for label, queryset in filtered_querysets.items()
    }
    cancelled_counts = {
        label: queryset.filter(status='cancelled').count()
        for label, queryset in filtered_querysets.items()
    }
    cancelled_total = sum(cancelled_counts.values())
    revenue_by_service = {}
    for label, queryset in filtered_querysets.items():
        total = queryset.filter(status='confirmed').aggregate(total=Sum(_amount_expression(label)))['total']
        revenue_by_service[label] = total or Decimal('0.00')

    # The recent-bookings panel applies both search and the selected date filter.
    recent_bookings = []
    for label, queryset in filtered_querysets.items():
        queryset = queryset.select_related('user')
        if search:
            queryset = queryset.filter(
                Q(booking_id__icontains=search)
                | Q(user__username__icontains=search)
            )
        for booking in queryset.order_by('-created_at')[:10]:
            user = getattr(booking, 'user', None)
            if label == 'Restaurants':
                amount = booking.average_cost * booking.guest_count
            else:
                amount = getattr(booking, REVENUE_FIELD[label])
            recent_bookings.append({
                'booking_id': str(booking.booking_id),
                'username': user.get_username() if user else 'Deleted user',
                'user_label': (
                    (user.get_full_name() or user.get_username())
                    if user else 'Deleted user'
                ),
                'service': label,
                'created_at': booking.created_at,
                'amount': amount,
                'status': booking.get_status_display(),
            })
    recent_bookings.sort(key=lambda item: item['created_at'], reverse=True)
    recent_bookings = recent_bookings[:10]

    service_labels = [label for label, _ in SERVICES]
    booking_counts = [counts[label] for label in service_labels]
    service_revenue = [float(revenue_by_service[label]) for label in service_labels]

    month_starts = _month_starts(today.replace(day=1))
    month_labels = [f'{month_name[value.month][:3]} {value.year}' for value in month_starts]
    month_totals = {value: Decimal('0.00') for value in month_starts}
    chart_start = month_starts[0]
    for label, model in SERVICES:
        rows = (
            model.objects.filter(created_at__date__gte=chart_start, status='confirmed')
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum(_amount_expression(label)))
        )
        for row in rows:
            month_value = row['month']
            month_key = month_value.date().replace(day=1) if hasattr(month_value, 'date') else month_value.replace(day=1)
            if month_key in month_totals:
                month_totals[month_key] += row['total'] or Decimal('0.00')

    daily_start = today - timedelta(days=13)
    daily_counts = {daily_start + timedelta(days=offset): 0 for offset in range(14)}
    for _, model in SERVICES:
        rows = (
            model.objects.filter(created_at__date__gte=daily_start, created_at__date__lte=today)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(total=Count('pk'))
        )
        for row in rows:
            if row['day'] in daily_counts:
                daily_counts[row['day']] += row['total']

    context = {
        'total_users': get_user_model().objects.count(),
        'total_bookings': sum(counts.values()),
        'total_revenue': sum(revenue_by_service.values(), Decimal('0.00')),
        'counts': counts,
        'cancelled_counts': cancelled_counts,
        'cancelled_total': cancelled_total,
        'latest_bookings': recent_bookings,
        'period': period,
        'search': search,
        'period_start': start_date,
        'period_end': end_date,
        'chart_service_labels': service_labels,
        'chart_booking_counts': booking_counts,
        'chart_service_revenue': service_revenue,
        'chart_month_labels': month_labels,
        'chart_month_revenue': [float(month_totals[value]) for value in month_starts],
        'chart_day_labels': [value.strftime('%d %b') for value in daily_counts],
        'chart_daily_bookings': list(daily_counts.values()),
    }
    return render(request, 'admin_dashboard/home.html', context)
