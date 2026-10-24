import io
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Image, Paragraph, Spacer, Table, TableStyle

from .common import banner, finish, para, qr_image, setup, status_chip, total_qr


ACCENT = colors.HexColor('#762b43')
ALLOWED_POSTER_HOSTS = {'image.tmdb.org', 'placehold.co'}


class PosterFallback(Flowable):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.width = 44 * mm
        self.height = 66 * mm

    def draw(self):
        self.canv.setFillColor(colors.HexColor('#241a21'))
        self.canv.roundRect(0, 0, self.width, self.height, 3 * mm, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor('#e8c7d0'))
        self.canv.setFont('Helvetica-Bold', 8)
        self.canv.drawCentredString(self.width / 2, self.height - 10 * mm, 'CINEMA')
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 9)
        title = (self.title[:28] + '...') if len(self.title) > 28 else self.title
        self.canv.drawCentredString(self.width / 2, self.height / 2, title)


def render(booking, data, qr_bytes):
    output, doc, styles, story = setup('Quadori Cinema Ticket', ACCENT, margins=(16, 16, 13, 13))
    story.extend([
        banner('CINEMA  ·  ADMIT ONE', ACCENT, font_size=12, padding=11),
        Spacer(1, 4 * mm), status_chip(data['status'], ACCENT), Spacer(1, 5 * mm),
    ])
    poster = _poster(booking.poster_url, booking.movie_name)
    movie_details = [
        para(booking.movie_name, styles['ServiceBig']),
        para(f'{booking.language} · {booking.genre} · {booking.duration} · Rated {booking.rating}', styles['ServiceSubtitle']),
        Spacer(1, 2 * mm),
        banner(f'{booking.theatre_name}  ·  {booking.city}', colors.HexColor('#f5eaf0'), font_size=10, padding=7),
        Spacer(1, 3 * mm),
        para('SHOW DATE', styles['ServiceSmall']),
        para(booking.show_date.strftime('%A, %d %b %Y'), styles['ServiceBody']),
        para('SHOW TIME', styles['ServiceSmall']),
        para(booking.show_time, styles['ServiceBig']),
        para('SEATS', styles['ServiceSmall']),
        para(', '.join(booking.seat_numbers or list(booking.reserved_seats.values_list('seat_number', flat=True))) or 'Not assigned', styles['ServiceBody']),
    ]
    details_column = Table([[item] for item in movie_details], colWidths=[117*mm])
    details_column.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    main = Table([[poster, details_column]], colWidths=[50*mm,124*mm])
    main.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(0,0),colors.HexColor('#f5eaf0')),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    story.extend([main, Spacer(1, 5 * mm)])
    stub = Table([[
        [para('BOOKING ID', styles['ServiceSmall']), para(data['booking_id'], styles['ServiceBody'])],
        [para('TICKET NUMBER', styles['ServiceSmall']), para(data['reference'], styles['ServiceBody'])],
    ], [
        [para('CUSTOMER', styles['ServiceSmall']), para(booking.customer_name, styles['ServiceBody'])],
        [para('BOOKED ON', styles['ServiceSmall']), para(data['booking_date'], styles['ServiceBody'])],
    ]], colWidths=[87*mm,87*mm])
    stub.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#fcf7f9')),
        ('BOX',(0,0),(-1,-1),.7,colors.HexColor('#d8bdc7')),
        ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#d8bdc7')),
        ('LINEBEFORE',(1,0),(1,-1),.5,colors.HexColor('#d8bdc7')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),
        ('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    story.extend([stub, Spacer(1, 5 * mm)])
    story.append(total_qr(data['amount'], ACCENT, qr_bytes, caption=f'{booking.seat_count} TICKET(S) - TOTAL', qr_size=30*mm))
    story.append(Spacer(1, 3 * mm))
    story.append(para(f'Customer contact: {booking.customer_email} · {booking.customer_phone}', styles['ServiceSmall']))
    return finish(output, doc, story)


def _poster(url, title):
    try:
        parsed = urlparse(url or '')
        if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_POSTER_HOSTS:
            return PosterFallback(title)
        request = Request(url, headers={'User-Agent': 'Quadori-Ticket/1.0'})
        with urlopen(request, timeout=4) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            return PosterFallback(title)
        image = PILImage.open(io.BytesIO(raw))
        image.thumbnail((500, 750))
        output = io.BytesIO()
        image.convert('RGB').save(output, format='JPEG', quality=82)
        output.seek(0)
        return Image(output, width=44 * mm, height=66 * mm)
    except Exception:
        return PosterFallback(title)
