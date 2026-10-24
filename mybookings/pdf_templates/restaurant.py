from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Spacer, Table, TableStyle

from .common import banner, finish, para, qr_image, setup, status_chip, total_qr


ACCENT = colors.HexColor('#b84b25')


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Restaurant Reservation Voucher', ACCENT, margins=(17, 17, 15, 15))
    story.extend([
        banner('TABLE RESERVATION', ACCENT, font_size=12, padding=11),
        Spacer(1, 4 * mm), status_chip(data['status'], ACCENT), Spacer(1, 6 * mm),
        para(booking.restaurant_name, styles['ServiceBig']),
        para(f'{booking.cuisine} · {booking.address}, {booking.city}', styles['ServiceSubtitle']),
    ])
    reservation = Table([[
        Table([[para('RESERVATION DATE', styles['ServiceSmall'])], [para(booking.booking_date.strftime('%A, %d %b %Y'), styles['ServiceBig'])]], colWidths=[71*mm]),
        Table([[para('ARRIVAL TIME', styles['ServiceSmall'])], [para(booking.booking_time.strftime('%I:%M %p'), styles['ServiceBig'])]], colWidths=[52*mm]),
        Table([[para('PARTY SIZE', styles['ServiceSmall'])], [para(f'{booking.guest_count} guests', styles['ServiceBig'])]], colWidths=[28*mm]),
    ]], colWidths=[77*mm,58*mm,33*mm])
    reservation.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fff1e9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBEFORE',(1,0),(-1,0),.6,colors.HexColor('#efc6b3')),
        ('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12),
    ]))
    story.extend([reservation, Spacer(1, 6 * mm)])
    ref_rows = [
        ('Booking ID', data['booking_id']), ('Reservation number', data['reference']),
        ('Booking status', data['status']), ('Reserved for', booking.customer_name),
        ('Contact', f'{booking.customer_phone} · {booking.customer_email}'),
        ('Opening hours', booking.opening_hours), ('Average cost', f'₹{booking.average_cost:,.2f} per guest'),
        ('Reservation made', data['booking_date']),
    ]
    refs = Table([[para(label, styles['ServiceSmall']), para(value, styles['ServiceBody'])] for label,value in ref_rows], colWidths=[43*mm,131*mm])
    refs.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,-1),colors.HexColor('#fff7f2')),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#f0ddd2')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
    ]))
    story.extend([refs, Spacer(1, 7 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes, caption='ESTIMATED PARTY COST', qr_size=28*mm))
    story.append(Spacer(1, 4 * mm))
    story.append(para('Please arrive on time and present this reservation voucher to the host.', styles['ServiceSmall']))
    return finish(output, doc, story)
