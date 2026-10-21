"""Render the same AR content as Word using the existing ReportLab dependency."""
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, LongTable, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, TableStyle,
)

from .ar_export import BODY, CAPTION, DRAFT, NOTE, _ReportContent, _render_activity_report, _text


class _PDFReport(_ReportContent):
    def __init__(self, payload):
        self.payload = payload
        self.story = []
        self.current_orientation = 'portrait'
        fontdir = Path(__file__).parent / 'fonts'
        for name, filename in [('ARRegular', 'DejaVuSans.ttf'), ('ARBold', 'DejaVuSans-Bold.ttf')]:
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(fontdir / filename)))
        self.styles = {
            BODY: ParagraphStyle('body', fontName='ARRegular', fontSize=10, leading=14, spaceAfter=7),
            NOTE: ParagraphStyle('note', fontName='ARRegular', fontSize=8, leading=11, spaceAfter=7),
            CAPTION: ParagraphStyle('caption', fontName='ARBold', fontSize=9, leading=12,
                                    spaceAfter=7, keepWithNext=True),
            'Civensa Madde': ParagraphStyle('bullet', fontName='ARRegular', fontSize=10,
                                          leading=14, leftIndent=12, spaceAfter=5,
                                          bulletFontName='ARRegular', bulletIndent=0),
            'Civensa Kapak Başlık': ParagraphStyle('cover', fontName='ARBold', fontSize=22,
                                                  leading=29, alignment=1, spaceAfter=18),
        }
        for level in range(1, 5):
            self.styles[f'Civensa Başlık {level}'] = ParagraphStyle(
                f'heading{level}', fontName='ARBold', fontSize=16 - level,
                leading=20 - level, spaceBefore=10, spaceAfter=8, keepWithNext=True)
        self.cell = ParagraphStyle('cell', fontName='ARRegular', fontSize=7, leading=10,
                                   wordWrap='CJK')
        self.cell_heading = ParagraphStyle('cellHeading', parent=self.cell, fontName='ARBold')

    @staticmethod
    def _paragraph(value, style):
        # User text must stay text, including angle brackets and ampersands.
        return Paragraph(escape(str(value)).replace('\n', '<br/>'), style)

    def _orientation(self, name):
        if name != self.current_orientation:
            self.story.extend([NextPageTemplate(name), PageBreak()])
            self.current_orientation = name

    def paragraph(self, text, style=BODY):
        self._orientation('portrait')
        paragraph = self._paragraph('' if text == '' else _text(text), self.styles[style])
        if style == 'Civensa Madde':
            paragraph.bulletText = '•'
        self.story.append(paragraph)

    def page_break(self):
        self.story.append(PageBreak())

    def toc(self, sections):
        for section in sections:
            if section['depth'] < 3:
                style = ParagraphStyle('toc', parent=self.styles[BODY],
                                       leftIndent=section['depth'] * 12)
                self.story.append(self._paragraph(section['title'], style))

    def table(self, headers, rows, title=None):
        if not headers:
            return
        wide = len(headers) > 6
        self._orientation('landscape' if wide else 'portrait')
        if title:
            self.story.append(self._paragraph(title, self.styles[CAPTION]))
        width = (landscape(A4) if wide else A4)[0] - 108
        data = [[self._paragraph(_text(value), self.cell_heading) for value in headers]]
        for row in rows:
            data.append([self._paragraph(_text(row[i] if i < len(row) else None), self.cell)
                         for i in range(len(headers))])
        table = LongTable(data, colWidths=[width / len(headers)] * len(headers),
                          repeatRows=1, splitByRow=1, splitInRow=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), .3, colors.HexColor('#bcc6d0')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9eff4')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        self.story.extend([table, Spacer(1, 10)])

    def decorate(self, canvas, doc):
        # Match Word's clean cover; mark every subsequent draft page.
        if doc.page == 1:
            return
        width, height = canvas._pagesize
        canvas.saveState()
        canvas.setFont('ARRegular', 8)
        if not self.payload['frozen']:
            canvas.drawString(54, height - 32, DRAFT)
        else:
            canvas.drawString(54, 30, f"Onaylı kopya · SHA-256: {self.payload['sha256'][:16]}")
        canvas.drawRightString(width - 54, 30, f'Sayfa {doc.page}')
        canvas.restoreState()


def build_activity_report_pdf(payload) -> bytes:
    report = _PDFReport(payload)
    _render_activity_report(report)
    output = BytesIO()
    # Fixed timestamps/document ID make repeated frozen downloads byte stable.
    doc = BaseDocTemplate(output, pagesize=A4, invariant=1,
                          title=f"{payload['year']} Faaliyet Raporu", author='Civensa')
    for name, size in [('portrait', A4), ('landscape', landscape(A4))]:
        width, height = size
        frame = Frame(54, 54, width - 108, height - 108,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        doc.addPageTemplates(PageTemplate(id=name, frames=[frame], pagesize=size,
                                          onPage=report.decorate))
    doc.build(report.story)
    return output.getvalue()
