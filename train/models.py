import uuid

from django.conf import settings
from django.db import models


class TrainBooking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    pnr_number = models.CharField(max_length=10, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='train_bookings',
    )
    train_code = models.CharField(max_length=20)
    train_number = models.CharField(max_length=10)
    train_name = models.CharField(max_length=120)
    source = models.CharField(max_length=80)
    destination = models.CharField(max_length=80)
    journey_date = models.DateField()
    travel_class = models.CharField(max_length=20)
    departure_time = models.CharField(max_length=10)
    arrival_time = models.CharField(max_length=10)
    duration = models.CharField(max_length=30)
    passenger_count = models.PositiveSmallIntegerField()
    passenger_details = models.JSONField(default=list)
    fare_per_passenger = models.DecimalField(max_digits=9, decimal_places=2)
    total_fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.pnr_number} — {self.train_number}'


class ReservedSeat(models.Model):
    booking = models.ForeignKey(
        TrainBooking,
        on_delete=models.CASCADE,
        related_name='reserved_seats',
    )
    train_code = models.CharField(max_length=20)
    journey_date = models.DateField()
    travel_class = models.CharField(max_length=20)
    seat_number = models.CharField(max_length=8)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('train_code', 'journey_date', 'travel_class', 'seat_number'),
                name='uniq_train_seat_date_class',
            ),
        ]
        ordering = ('seat_number',)

    def __str__(self):
        return f'{self.train_code} {self.travel_class} {self.journey_date} seat {self.seat_number}'
