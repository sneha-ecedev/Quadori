import secrets
import string

from django.db import migrations, models


def fill_booking_numbers(apps, schema_editor):
    MovieBooking = apps.get_model('movie', 'MovieBooking')
    db_alias = schema_editor.connection.alias
    used = set(MovieBooking.objects.using(db_alias).exclude(
        booking_number__isnull=True,
    ).values_list('booking_number', flat=True))
    for booking in MovieBooking.objects.using(db_alias).filter(booking_number__isnull=True).iterator():
        while True:
            number = ''.join(secrets.choice(string.digits) for _ in range(10))
            if number not in used:
                used.add(number)
                booking.booking_number = number
                booking.save(update_fields=['booking_number'])
                break


class Migration(migrations.Migration):
    dependencies = [('movie', '0001_initial')]

    operations = [
        migrations.AddField(
            model_name='moviebooking',
            name='booking_number',
            field=models.CharField(max_length=10, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='moviebooking',
            name='movie_description',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(fill_booking_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='moviebooking',
            name='booking_number',
            field=models.CharField(max_length=10, unique=True, editable=False),
        ),
    ]
