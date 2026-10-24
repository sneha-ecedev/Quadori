import uuid

from django.conf import settings
from django.db import models


class BusBooking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bus_bookings',
    )
    bus_code = models.CharField(max_length=20)
    operator = models.CharField(max_length=100)
    bus_number = models.CharField(max_length=30)
    bus_type = models.CharField(max_length=60)
    source = models.CharField(max_length=80)
    destination = models.CharField(max_length=80)
    journey_date = models.DateField()
    departure_time = models.CharField(max_length=10)
    arrival_time = models.CharField(max_length=10)
    duration = models.CharField(max_length=30)
    seat_count = models.PositiveSmallIntegerField()
    passenger_details = models.JSONField(default=list)
    fare_per_seat = models.DecimalField(max_digits=8, decimal_places=2)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.operator} booking {self.booking_id}'


class ReservedSeat(models.Model):
    booking = models.ForeignKey(
        BusBooking,
        on_delete=models.CASCADE,
        related_name='reserved_seats',
    )
    bus_code = models.CharField(max_length=20)
    journey_date = models.DateField()
    seat_number = models.CharField(max_length=5)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('bus_code', 'journey_date', 'seat_number'),
                name='unique_bus_seat_per_journey',
            ),
        ]
        ordering = ('seat_number',)

    def __str__(self):
        return f'{self.bus_code} {self.journey_date} seat {self.seat_number}'
