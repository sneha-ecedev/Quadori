import uuid
import secrets
import string

from django.conf import settings
from django.db import models


def generate_booking_number():
    return ''.join(secrets.choice(string.digits) for _ in range(10))


class MovieBooking(models.Model):
    booking_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    booking_number = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movie_bookings',
    )
    movie_code = models.CharField(max_length=40)
    movie_name = models.CharField(max_length=150)
    movie_description = models.TextField(blank=True)
    poster_url = models.URLField(max_length=500)
    language = models.CharField(max_length=50)
    genre = models.CharField(max_length=80)
    duration = models.CharField(max_length=30)
    rating = models.CharField(max_length=10)
    city = models.CharField(max_length=80)
    theatre_code = models.CharField(max_length=50)
    theatre_name = models.CharField(max_length=150)
    show_date = models.DateField()
    show_time = models.CharField(max_length=20)
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2)
    seat_count = models.PositiveSmallIntegerField()
    seat_numbers = models.JSONField(default=list, blank=True)
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=(('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')), default='confirmed')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_number:
            while True:
                candidate = generate_booking_number()
                if not type(self).objects.filter(booking_number=candidate).exists():
                    self.booking_number = candidate
                    break
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.movie_name} booking {self.booking_id}'


class ReservedSeat(models.Model):
    booking = models.ForeignKey(
        MovieBooking,
        on_delete=models.CASCADE,
        related_name='reserved_seats',
    )
    movie_code = models.CharField(max_length=40)
    theatre_code = models.CharField(max_length=50)
    show_date = models.DateField()
    show_time = models.CharField(max_length=20)
    seat_number = models.CharField(max_length=8)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('movie_code', 'theatre_code', 'show_date', 'show_time', 'seat_number'),
                name='uniq_movie_seat_show',
            ),
        ]
        ordering = ('seat_number',)

    def __str__(self):
        return f'{self.movie_code} {self.show_date} {self.show_time} seat {self.seat_number}'
