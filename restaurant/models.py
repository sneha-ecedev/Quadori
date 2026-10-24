import uuid

from django.conf import settings
from django.db import models


class RestaurantBooking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='restaurant_bookings',
    )
    restaurant_code = models.CharField(max_length=40)
    restaurant_name = models.CharField(max_length=150)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=80)
    cuisine = models.CharField(max_length=40)
    opening_hours = models.CharField(max_length=60)
    average_cost = models.DecimalField(max_digits=8, decimal_places=2)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    guest_count = models.PositiveSmallIntegerField()
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.restaurant_name} reservation {self.booking_id}'
