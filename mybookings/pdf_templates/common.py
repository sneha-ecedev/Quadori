import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


INK = colors.HexColor('#1d2d45')
MUTED = colors.HexColor('#65758b')
LINE = colors.HexColor('#d9e1ec')
PALE = colors.HexColor('#f3f6fa')


class BrandMark(Flowable):
    def __init__(self, accent):
        super().__init__()
        self.accent = accent
        self.width = 174 * mm
        self.height = 15 * mm

    def draw(self):
        self.canv.setFillColor(self.accent)
        self.canv.circle(6 * mm, 7 * mm, 5 * mm, fill=1, stroke=0)
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 9)
        self.canv.drawCentredString(6 * mm, 4 * mm, 'Q')
        self.canv.setFillColor(INK)
        self.canv.setFont('Helvetica-Bold', 19)
        self.canv.drawString(14 * mm, 2 * mm, 'Quadori')
        self.canv.setFillColor(MUTED)
        self.canv.setFont('Helvetica', 8)
        self.canv.drawRightString(self.width, 4 * mm, 'TRAVEL & EXPERIENCES')


def setup(title, accent, *, margins=(15, 15, 15, 15)):
    output = io.BytesIO()
    left, right, top, bottom = (value * mm for value in margins)
    doc = SimpleDocTemplate(
        output, pagesize=A4, leftMargin=left, rightMargin=right,
        topMargin=top, bottomMargin=bottom, title=title, author='Quadori',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ServiceTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=19, leading=23, textColor=accent, alignment=0, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name='ServiceSubtitle', parent=styles['BodyText'], fontSize=9,
        leading=13, textColor=MUTED, spaceAfter=3 * mm,
    ))
    styles.add(ParagraphStyle(
        name='ServiceBody', parent=styles['BodyText'], fontSize=9,
        leading=13, textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name='ServiceSmall', parent=styles['BodyText'], fontSize=7.5,
        leading=10, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='ServiceBig', parent=styles['BodyText'], fontName='Helvetica-Bold',
        fontSize=17, leading=20, textColor=INK,
    ))
    story = [BrandMark(accent), Spacer(1, 4 * mm)]
    return output, doc, styles, story


def finish(output, doc, story):
    doc.build(story)
    return output.getvalue()


def para(value, style):
    return Paragraph(escape(str(value or '—')), style)


def qr_image(qr_bytes, size=30 * mm):
    return Image(io.BytesIO(qr_bytes), width=size, height=size)


def kv_table(rows, widths, *, accent, background=colors.white, padding=7):
    cells = [[para(label, _label_style()), para(value, _body_style())] for label, value in rows]
    table = Table(cells, colWidths=widths, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, -1), PALE),
        ('BACKGROUND', (1, 0), (1, -1), background),
        ('LINEBELOW', (0, 0), (-1, -1), .4, LINE),
        ('LINEBEFORE', (0, 0), (0, -1), 2, accent),
        ('LEFTPADDING', (0, 0), (-1, -1), padding),
        ('RIGHTPADDING', (0, 0), (-1, -1), padding),
        ('TOPPADDING', (0, 0), (-1, -1), padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
    ]))
    return table


def banner(text, accent, *, font_size=10, padding=8):
    style = ParagraphStyle(
        name=f'Banner{abs(hash((text, str(accent))))}', fontName='Helvetica-Bold',
        fontSize=font_size, leading=font_size + 4, textColor=colors.white,
    )
    table = Table([[Paragraph(escape(str(text)), style)]], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent),
        ('LEFTPADDING', (0, 0), (-1, -1), padding),
        ('RIGHTPADDING', (0, 0), (-1, -1), padding),
        ('TOPPADDING', (0, 0), (-1, -1), padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
    ]))
    return table


def status_chip(status, accent):
    color = colors.HexColor('#b42318') if status == 'Cancelled' else accent
    return banner(f'BOOKING STATUS  ·  {status.upper()}', color, font_size=8, padding=6)


def passenger_list(people, styles, *, accent, heading='Passenger Details'):
    rows = [[banner(heading.upper(), accent, font_size=8, padding=6)]]
    for person in people or ['No passenger or guest details recorded']:
        rows.append([para(person, styles['ServiceBody'])])
    table = Table(rows, colWidths=[174 * mm], hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), .6, LINE),
        ('LINEBELOW', (0, 1), (-1, -2), .35, LINE),
        ('LEFTPADDING', (0, 1), (-1, -1), 8),
        ('RIGHTPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
    ]))
    return table


def money_total(amount, accent, caption='TOTAL'):
    style = ParagraphStyle(
        name=f'Total{abs(hash((amount, caption)))}', fontName='Helvetica-Bold',
        fontSize=14, leading=18, textColor=colors.white,
    )
    table = Table([[Paragraph(escape(caption), ParagraphStyle(
        name=f'TotalLabel{abs(hash(caption))}', fontName='Helvetica-Bold',
        fontSize=8, textColor=colors.white,
    )), Paragraph(escape(str(amount)), style)]], colWidths=[83 * mm, 42 * mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), accent), ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 9), ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def total_qr(amount, accent, qr_bytes, *, caption='TOTAL', qr_size=27 * mm):
    table = Table(
        [[money_total(amount, accent, caption), qr_image(qr_bytes, qr_size)]],
        colWidths=[137 * mm, qr_size],
    )
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return table


def _label_style():
    return ParagraphStyle(name='TicketLabel', fontName='Helvetica-Bold', fontSize=8, leading=11, textColor=MUTED)


def _body_style():
    return ParagraphStyle(name='TicketKVBody', fontName='Helvetica', fontSize=9, leading=13, textColor=INK)
