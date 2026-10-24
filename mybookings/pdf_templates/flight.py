from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from .common import banner, finish, para, passenger_list, setup, status_chip, total_qr


ACCENT = colors.HexColor('#1457a6')


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Flight Boarding Pass', ACCENT, margins=(13, 13, 12, 12))
    story.extend([
        banner('FLIGHT BOARDING PASS', ACCENT, font_size=11, padding=9),
        Spacer(1, 5 * mm), status_chip(data['status'], ACCENT), Spacer(1, 4 * mm),
    ])
    route = Table([[
        Table([[para('FROM', styles['ServiceSmall'])], [para(booking.from_city, styles['ServiceBig'])]], colWidths=[64*mm]),
        para('FLIGHT', styles['ServiceSmall']),
        Table([[para('TO', styles['ServiceSmall'])], [para(booking.to_city, styles['ServiceBig'])]], colWidths=[64*mm]),
    ]], colWidths=[68 * mm, 25 * mm, 68 * mm])
    route.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef5ff')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 10), ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.extend([route, Spacer(1, 4 * mm)])
    flight_info = [
        ('AIRLINE', booking.airline_name), ('FLIGHT', booking.flight_number),
        ('DATE', booking.flight_date.strftime('%a, %d %b %Y')),
        ('DEPARTURE', booking.departure_time), ('ARRIVAL', booking.arrival_time),
        ('DURATION', booking.duration), ('PNR', booking.pnr_number),
        ('BOOKING ID', data['booking_id']), ('BOOKED ON', data['booking_date']),
        ('CUSTOMER', data['customer']),
    ]
    rows = []
    for index in range(0, len(flight_info), 2):
        left, right = flight_info[index:index + 2]
        rows.append([_cell(left, styles), _cell(right, styles)])
    info = Table(rows, colWidths=[82 * mm, 82 * mm])
    info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white), ('BOX', (0, 0), (-1, -1), .7, ACCENT),
        ('INNERGRID', (0, 0), (-1, -1), .35, colors.HexColor('#d5e1ef')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([info, Spacer(1, 4 * mm), passenger_list(data['people'], styles, accent=ACCENT), Spacer(1, 4 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes))
    return finish(output, doc, story)


def _cell(item, styles):
    return [para(item[0], styles['ServiceSmall']), para(item[1], styles['ServiceBody'])]
