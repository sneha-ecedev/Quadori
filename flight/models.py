import uuid

from django.conf import settings
from django.db import models


class Booking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    pnr_number = models.CharField(max_length=6, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flight_bookings',
    )
    flight_date = models.DateField()
    airline_name = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=20)
    from_city = models.CharField(max_length=80)
    to_city = models.CharField(max_length=80)
    departure_time = models.CharField(max_length=10)
    arrival_time = models.CharField(max_length=10)
    duration = models.CharField(max_length=30)
    passenger_count = models.PositiveSmallIntegerField()
    passenger_details = models.JSONField(default=list)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.pnr_number} — {self.flight_number}'
