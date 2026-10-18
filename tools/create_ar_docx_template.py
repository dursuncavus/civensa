"""Create the initial CIV-046 template. Subsequent design edits belong in Word."""
from pathlib import Path
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor


def create(path):
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.top_margin = section.bottom_margin = Mm(22)
    section.left_margin = section.right_margin = Mm(20)
    section.header_distance = section.footer_distance = Mm(10)
    styles = doc.styles
    body = styles.add_style('Civensa Gövde', WD_STYLE_TYPE.PARAGRAPH)
    body.base_style = styles['Normal']
    body.font.name = 'DejaVu Sans'
    body.font.size = Pt(10)
    body.font.color.rgb = RGBColor.from_string('243746')
    body.paragraph_format.space_after = Pt(7)
    body.paragraph_format.widow_control = True
    for depth, size in enumerate([18, 14, 12, 11], 1):
        style = styles.add_style(f'Civensa Başlık {depth}', WD_STYLE_TYPE.PARAGRAPH)
        style.base_style = body
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string('164E63')
        style.paragraph_format.space_before = Pt(15 if depth == 1 else 10)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
        outline = OxmlElement('w:outlineLvl')
        outline.set(qn('w:val'), str(depth - 1))
        style.element.get_or_add_pPr().append(outline)
    bullet = styles.add_style('Civensa Madde', WD_STYLE_TYPE.PARAGRAPH)
    bullet.base_style = body
    # Reuse the template's real Word bullet definition, without literal bullet text.
    numpr = OxmlElement('w:numPr')
    numid = OxmlElement('w:numId')
    numid.set(qn('w:val'), '1')
    numpr.append(numid)
    bullet.element.get_or_add_pPr().append(numpr)
    bullet.paragraph_format.left_indent = Mm(5)
    bullet.paragraph_format.first_line_indent = Mm(-3)
    table = styles.add_style('Civensa Tablo', WD_STYLE_TYPE.TABLE)
    table.base_style = styles['Table Grid']
    table.font.name = body.font.name
    table.font.size = Pt(9)
    caption = styles.add_style('Civensa Tablo Başlık', WD_STYLE_TYPE.PARAGRAPH)
    caption.base_style = body
    caption.font.bold = True
    caption.font.size = Pt(9)
    caption.paragraph_format.keep_with_next = True
    caption.paragraph_format.space_after = Pt(4)
    note = styles.add_style('Civensa Not', WD_STYLE_TYPE.PARAGRAPH)
    note.base_style = body
    note.font.size = Pt(8)
    note.font.color.rgb = RGBColor.from_string('52616B')
    note.paragraph_format.space_before = Pt(4)
    note.paragraph_format.space_after = Pt(8)
    shade = OxmlElement('w:shd')
    shade.set(qn('w:fill'), 'F0F4F6')
    note.element.get_or_add_pPr().append(shade)
    cover = styles.add_style('Civensa Kapak Başlık', WD_STYLE_TYPE.PARAGRAPH)
    cover.base_style = body
    cover.font.size = Pt(24)
    cover.font.bold = True
    cover.font.color.rgb = RGBColor.from_string('164E63')
    cover.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.paragraph_format.space_before = Pt(28)
    cover.paragraph_format.space_after = Pt(14)
    doc.core_properties.title = 'Civensa Faaliyet Raporu Word Şablonu'
    doc.core_properties.author = 'Civensa'
    doc.add_paragraph('Bu belgenin Civensa stillerini Word’de düzenleyip aynı adla kaydedin.', body)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


if __name__ == '__main__':
    create(Path(__file__).resolve().parents[1] / 'app/templates_docx/faaliyet_raporu.docx')
