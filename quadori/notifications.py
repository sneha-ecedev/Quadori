import base64
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMessage


logger = logging.getLogger(__name__)


def send_booking_confirmation(
    *, recipient, customer_name, booking_id, reference,
    service_name, booking_date, booking_time, amount,
):
    """Send a booking receipt without allowing mail failures to affect a booking."""
    if not recipient:
        logger.warning(
            'Skipping %s confirmation email for booking %s: no recipient address.',
            service_name,
            booking_id,
        )
        return False
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.error(
            'Cannot send %s confirmation for booking %s: Gmail SMTP credentials are not configured.',
            service_name,
            booking_id,
        )
        return False

    subject = f'Quadori {service_name} booking confirmed — {reference}'
    body = (
        f'Hello {customer_name},\n\n'
        'Thank you for booking with Quadori. Your booking is confirmed.\n\n'
        f'Customer Name: {customer_name}\n'
        f'Booking ID: {booking_id}\n'
        f'Booking Number / PNR: {reference}\n'
        f'Service Name: {service_name}\n'
        f'Date: {booking_date}\n'
        f'Time: {booking_time}\n'
        f'Amount: ₹{amount:,.2f}\n\n'
        'Thank you for choosing Quadori. We hope you enjoy your experience!\n'
    )

    try:
        message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.send(fail_silently=False)
    except Exception:
        logger.exception(
            'Unable to send %s confirmation email for booking %s.',
            service_name,
            booking_id,
        )
        return False
    return True


def send_booking_cancellation_email(
    *, recipient, customer_name, booking_id, reference,
    service_name, booking_date, booking_time, amount,
):
    """Send a cancellation notice without affecting the cancellation operation."""
    if not recipient or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        logger.warning('Skipping %s cancellation email for booking %s: recipient or SMTP credentials missing.', service_name, booking_id)
        return False
    try:
        EmailMessage(
            subject=f'Quadori {service_name} cancelled — {reference}',
            body=(
                f'Hello {customer_name},\n\nYour Quadori booking has been cancelled.\n\n'
                f'Customer Name: {customer_name}\nBooking ID: {booking_id}\n'
                f'Booking Number / PNR: {reference}\nService Name: {service_name}\n'
                f'Date: {booking_date}\nTime: {booking_time}\nAmount: ₹{amount:,.2f}\n\n'
                'Thank you for choosing Quadori.\n'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        ).send(fail_silently=False)
    except Exception:
        logger.exception('Unable to send %s cancellation email for booking %s.', service_name, booking_id)
        return False
    return True


def _to_e164(phone_number):
    """Normalize an entered phone number for Twilio without changing its destination."""
    raw_number = str(phone_number or '').strip()
    digits = re.sub(r'\D', '', raw_number)
    if raw_number.startswith('+'):
        normalized = f'+{digits}'
    elif raw_number.startswith('00'):
        normalized = f'+{digits[2:]}'
    else:
        country_code = re.sub(r'\D', '', settings.TWILIO_DEFAULT_COUNTRY_CODE)
        if raw_number.startswith('0') and country_code and len(digits) == 11:
            normalized = f'+{country_code}{digits[1:]}'
        elif len(digits) == 10 and country_code:
            normalized = f'+{country_code}{digits}'
        elif country_code and digits.startswith(country_code) and 11 <= len(digits) <= 15:
            normalized = f'+{digits}'
        else:
            normalized = ''
    return normalized if re.fullmatch(r'\+[1-9]\d{7,14}', normalized) else None


def send_booking_sms(
    *, recipient, customer_name, booking_id, reference,
    service_name, booking_date, booking_time, amount,
):
    """Send a Twilio booking SMS; provider failures never affect booking completion."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_FROM_NUMBER:
        logger.error(
            'Cannot send %s SMS for booking %s: Twilio credentials or sender number are not configured.',
            service_name,
            booking_id,
        )
        return False

    destination = _to_e164(recipient)
    if destination is None:
        logger.warning(
            'Skipping %s SMS for booking %s: customer phone number is not a valid international number.',
            service_name,
            booking_id,
        )
        return False

    body = (
        f'Quadori: {service_name} confirmed for {customer_name}. '
        f'Ref {reference}; ID {booking_id}; {booking_date}, {booking_time}; '
        f'INR {amount:,.2f}. Thank you!'
    )
    account_sid = settings.TWILIO_ACCOUNT_SID
    endpoint = (
        f'https://api.twilio.com/2010-04-01/Accounts/'
        f'{quote(account_sid, safe="")}/Messages.json'
    )
    credentials = base64.b64encode(
        f'{account_sid}:{settings.TWILIO_AUTH_TOKEN}'.encode('utf-8'),
    ).decode('ascii')
    request = Request(
        endpoint,
        data=urlencode({
            'To': destination,
            'From': settings.TWILIO_FROM_NUMBER,
            'Body': body,
        }).encode('utf-8'),
        headers={
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )
    try:
        with urlopen(request, timeout=10) as response:
            if response.status not in (200, 201):
                logger.warning(
                    'Twilio returned HTTP %s for %s SMS booking %s.',
                    response.status,
                    service_name,
                    booking_id,
                )
                return False
    except HTTPError as error:
        logger.warning(
            'Twilio returned HTTP %s for %s SMS booking %s.',
            error.code,
            service_name,
            booking_id,
        )
        return False
    except (URLError, TimeoutError, OSError):
        logger.exception(
            'Unable to send %s SMS for booking %s.',
            service_name,
            booking_id,
        )
        return False
    except Exception:
        logger.exception(
            'Unexpected error sending %s SMS for booking %s.',
            service_name,
            booking_id,
        )
        return False
    return True


def send_booking_cancellation_sms(
    *, recipient, customer_name, booking_id, reference,
    service_name, booking_date, booking_time, amount,
):
    """Send a Twilio cancellation SMS; notification failures never affect cancellation."""
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_FROM_NUMBER:
        logger.warning('Skipping %s cancellation SMS for booking %s: Twilio is not configured.', service_name, booking_id)
        return False
    destination = _to_e164(recipient)
    if destination is None:
        logger.warning('Skipping %s cancellation SMS for booking %s: invalid customer phone.', service_name, booking_id)
        return False
    body = (
        f'Quadori: {service_name} cancelled for {customer_name}. Ref {reference}; '
        f'ID {booking_id}; {booking_date}, {booking_time}. Contact support if you need help.'
    )
    account_sid = settings.TWILIO_ACCOUNT_SID
    endpoint = f'https://api.twilio.com/2010-04-01/Accounts/{quote(account_sid, safe="")}/Messages.json'
    credentials = base64.b64encode(f'{account_sid}:{settings.TWILIO_AUTH_TOKEN}'.encode('utf-8')).decode('ascii')
    request = Request(
        endpoint,
        data=urlencode({'To': destination, 'From': settings.TWILIO_FROM_NUMBER, 'Body': body}).encode('utf-8'),
        headers={'Authorization': f'Basic {credentials}', 'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=10) as response:
            if response.status not in (200, 201):
                logger.warning('Twilio returned HTTP %s for %s cancellation SMS booking %s.', response.status, service_name, booking_id)
                return False
    except HTTPError as error:
        logger.warning('Twilio returned HTTP %s for %s cancellation SMS booking %s.', error.code, service_name, booking_id)
        return False
    except Exception:
        logger.exception('Unable to send %s cancellation SMS for booking %s.', service_name, booking_id)
        return False
    return True
