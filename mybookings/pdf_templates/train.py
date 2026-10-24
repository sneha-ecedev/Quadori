from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, Table, TableStyle

from .common import banner, finish, para, passenger_list, qr_image, setup, status_chip, total_qr


ACCENT = colors.HexColor('#196b49')


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Indian Railways E-Ticket', ACCENT, margins=(14, 14, 12, 12))
    story.extend([
        banner('INDIAN RAILWAYS  ·  ELECTRONIC RESERVATION', ACCENT, font_size=10, padding=9),
        Spacer(1, 3 * mm), para(f'PNR  {booking.pnr_number}', styles['ServiceBig']),
        status_chip(data['status'], ACCENT), Spacer(1, 4 * mm),
    ])
    story.append(banner(f'{booking.train_name}  ·  {booking.train_number}', colors.HexColor('#e9f4ee'), font_size=10, padding=8))
    story.append(Spacer(1, 3 * mm))
    route = Table([[
        Table([[para('FROM', styles['ServiceSmall'])], [para(booking.source, styles['ServiceBig'])], [para(booking.departure_time, styles['ServiceBody'])]], colWidths=[61*mm]),
        para('TO', styles['ServiceSmall']),
        Table([[para('TO', styles['ServiceSmall'])], [para(booking.destination, styles['ServiceBig'])], [para(booking.arrival_time, styles['ServiceBody'])]], colWidths=[61*mm]),
    ]], colWidths=[65*mm,20*mm,65*mm])
    route.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f7f2')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('ALIGN',(1,0),(1,0),'CENTER'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    story.extend([route, Spacer(1, 4 * mm)])
    journey_rows = [
        ('Date of journey', booking.journey_date.strftime('%A, %d %b %Y')),
        ('Class', booking.travel_class), ('Duration', booking.duration),
        ('Booking ID', data['booking_id']), ('Booked by', data['customer']),
        ('Booking date', data['booking_date']), ('Berths', ', '.join(_berths(booking))),
    ]
    story.append(Table([[para(label, styles['ServiceSmall']), para(value, styles['ServiceBody'])] for label,value in journey_rows], colWidths=[46*mm,104*mm], style=TableStyle([
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#edf5ef')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d5e4d9')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ])))
    story.extend([Spacer(1, 4 * mm), passenger_list(data['people'], styles, accent=ACCENT, heading='Passenger / Berth Allocation'), Spacer(1, 4 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes, caption='TOTAL FARE'))
    story.append(Spacer(1, 2 * mm))
    story.append(para('Carry a valid photo ID during your journey. This ticket is an electronic booking record.', styles['ServiceSmall']))
    return finish(output, doc, story)


def _berths(booking):
    assigned = [p.get('seat_number') for p in booking.passenger_details or [] if p.get('seat_number')]
    return assigned or list(booking.reserved_seats.values_list('seat_number', flat=True))
