import uuid

from django.conf import settings
from django.db import models


class HotelBooking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hotel_bookings',
    )
    hotel_code = models.CharField(max_length=40)
    hotel_name = models.CharField(max_length=150)
    image_url = models.URLField(max_length=500)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=80)
    check_in = models.DateField()
    check_out = models.DateField()
    nights = models.PositiveSmallIntegerField()
    guest_count = models.PositiveSmallIntegerField()
    adult_count = models.PositiveSmallIntegerField(default=1)
    child_count = models.PositiveSmallIntegerField(default=0)
    room_count = models.PositiveSmallIntegerField()
    room_type = models.CharField(max_length=20)
    guest_details = models.JSONField(default=list)
    price_per_room_night = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.hotel_name} booking {self.booking_id}'
