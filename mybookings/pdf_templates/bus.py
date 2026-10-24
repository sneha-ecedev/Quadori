from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, Table, TableStyle

from .common import banner, finish, para, passenger_list, qr_image, setup, status_chip, total_qr


ACCENT = colors.HexColor('#13836b')


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Bus Ticket', ACCENT, margins=(14, 14, 13, 13))
    story.extend([
        banner(f'{booking.operator.upper()}  ·  BUS TICKET', ACCENT, font_size=12, padding=11),
        Spacer(1, 4 * mm), status_chip(data['status'], ACCENT), Spacer(1, 4 * mm),
    ])
    journey = Table([[
        Table([[para('BOARDING POINT', styles['ServiceSmall'])], [para(booking.source, styles['ServiceBig'])]], colWidths=[75*mm]),
        Table([[para('DESTINATION', styles['ServiceSmall'])], [para(booking.destination, styles['ServiceBig'])]], colWidths=[75*mm]),
    ]], colWidths=[82 * mm, 82 * mm])
    journey.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#e8f6f2')),
        ('LINEBEFORE',(1,0),(1,0),1,ACCENT),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),11),
        ('BOTTOMPADDING',(0,0),(-1,-1),11),
    ]))
    story.extend([journey, Spacer(1, 5 * mm)])
    facts = [
        ['Bus number', booking.bus_number, 'Bus type', booking.bus_type],
        ['Journey date', booking.journey_date.strftime('%A, %d %b %Y'), 'Departure', booking.departure_time],
        ['Arrival', booking.arrival_time, 'Duration', booking.duration],
        ['Booking reference', data['reference'], 'Booking ID', data['booking_id']],
        ['Booked by', data['customer'], 'Booked on', data['booking_date']],
        ['Seat(s)', ', '.join(_seats(booking)), 'Passengers', str(booking.seat_count)],
    ]
    details = Table([[para(a, styles['ServiceSmall']), para(b, styles['ServiceBody']), para(c, styles['ServiceSmall']), para(d, styles['ServiceBody'])] for a,b,c,d in facts], colWidths=[31*mm,51*mm,29*mm,53*mm])
    details.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eff8f5')),
        ('BACKGROUND',(2,0),(2,-1),colors.HexColor('#eff8f5')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#cfe4dd')),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    story.extend([details, Spacer(1, 5 * mm), passenger_list(data['people'], styles, accent=ACCENT), Spacer(1, 5 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes, caption='FARE PAID / DUE'))
    story.append(para('Please arrive at the boarding point before departure.', styles['ServiceSmall']))
    return finish(output, doc, story)


def _seats(booking):
    from_passengers = [p.get('seat_number') for p in booking.passenger_details or [] if p.get('seat_number')]
    if from_passengers:
        return from_passengers
    return list(booking.reserved_seats.values_list('seat_number', flat=True))
