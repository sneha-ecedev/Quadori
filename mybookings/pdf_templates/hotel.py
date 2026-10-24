from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, Table, TableStyle

from .common import banner, finish, para, passenger_list, qr_image, setup, status_chip, total_qr


ACCENT = colors.HexColor('#9a6b24')


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Hotel Booking Voucher', ACCENT, margins=(16, 16, 14, 14))
    story.extend([
        banner('HOTEL BOOKING VOUCHER', ACCENT, font_size=12, padding=11),
        Spacer(1, 4 * mm), status_chip(data['status'], ACCENT), Spacer(1, 4 * mm),
        para(booking.hotel_name, styles['ServiceBig']),
        para(f'{booking.address}, {booking.city}', styles['ServiceSubtitle']),
    ])
    stay = Table([[
        Table([[para('CHECK-IN', styles['ServiceSmall'])], [para(booking.check_in.strftime('%a, %d %b %Y'), styles['ServiceBig'])]], colWidths=[60*mm]),
        Table([[para('CHECK-OUT', styles['ServiceSmall'])], [para(booking.check_out.strftime('%a, %d %b %Y'), styles['ServiceBig'])]], colWidths=[60*mm]),
        Table([[para('NIGHTS', styles['ServiceSmall'])], [para(str(booking.nights), styles['ServiceBig'])]], colWidths=[31*mm]),
    ]], colWidths=[66*mm,66*mm,36*mm])
    stay.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fbf5e9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBEFORE',(1,0),(-1,0),.6,colors.HexColor('#dfc996')),
        ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),11),
    ]))
    story.extend([stay, Spacer(1, 5 * mm)])
    guest_rows = [
        ('Primary guest', data['customer']), ('Booking reference', data['reference']),
        ('Booking ID', data['booking_id']), ('Booking status', data['status']),
        ('Room selection', f'{booking.room_count} × {booking.room_type}'),
        ('Occupancy', f'{booking.adult_count} adults · {booking.child_count} children · {booking.guest_count} guests'),
        ('Check-in time', 'Confirm with the hotel'), ('Booked on', data['booking_date']),
    ]
    guest_table = Table([[para(label, styles['ServiceSmall']), para(value, styles['ServiceBody'])] for label,value in guest_rows], colWidths=[43*mm,131*mm])
    guest_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#f8f3e9')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#e6dcc6')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    story.extend([guest_table, Spacer(1, 5 * mm), passenger_list(data['people'], styles, accent=ACCENT, heading='Registered Guests'), Spacer(1, 5 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes, caption='TOTAL STAY PRICE', qr_size=28*mm))
    story.append(Spacer(1, 3 * mm))
    story.append(para('Present this voucher and a valid photo ID at check-in.', styles['ServiceSmall']))
    return finish(output, doc, story)
