"""Render the six explicit Markdown sections as a six-page PDF (reportlab)."""
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports'
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyCustom', fontName='Helvetica',fontSize=9.8,leading=13.6,
                          spaceAfter=8,textColor=colors.HexColor('#263649')))
styles.add(ParagraphStyle(name='TitleCustom',fontName='Helvetica-Bold',fontSize=23,leading=27,
                          spaceAfter=14,textColor=colors.HexColor('#16324f')))
styles.add(ParagraphStyle(name='HeadingCustom',fontName='Helvetica-Bold',fontSize=15,leading=19,
                          spaceAfter=12,textColor=colors.HexColor('#16324f')))
styles.add(ParagraphStyle(name='CellCustom',fontName='Helvetica',fontSize=8.4,leading=11,
                          textColor=colors.HexColor('#263649')))


def inline(text):
    text = escape(text)
    text = re.sub(r'`([^`]+)`',r'<font name="Courier" size="8.4">\1</font>',text)
    return text


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#d4dce5'))
    canvas.line(42,36,A4[0]-42,36)
    canvas.setFont('Helvetica',8)
    canvas.setFillColor(colors.HexColor('#67778b'))
    canvas.drawString(42,23,'ATOMITY FORECASTING CHALLENGE  /  data-v1')
    canvas.drawRightString(A4[0]-42,23,str(doc.page))


def main():
    source = (REPORT/'final_report.md').read_text(encoding='utf-8')
    pages = source.split('\n---\n')
    story = []
    width = A4[0]-84
    for page_no, page in enumerate(pages):
        if page_no:
            story.append(PageBreak())
        blocks = page.strip().split('\n\n')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if block.startswith('# '):
                story.append(Paragraph(inline(block[2:]),styles['TitleCustom']))
            elif block.startswith('## '):
                story.append(Paragraph(inline(block[3:]),styles['HeadingCustom']))
            elif block.startswith('!['):
                relative = re.search(r'\]\((.*?)\)',block).group(1)
                picture = Image(str(REPORT/relative))
                ratio = width/picture.imageWidth
                picture.drawWidth, picture.drawHeight = width, picture.imageHeight*ratio
                # Keep the forecast figure compact enough for the error discussion.
                if picture.drawHeight > 235:
                    picture.drawHeight = 235
                    picture.drawWidth = picture.imageWidth*235/picture.imageHeight
                story.extend([picture,Spacer(1,8)])
            elif block.startswith('|'):
                rows = []
                for line in block.splitlines():
                    if re.match(r'^\|[\s:|-]+\|$',line):
                        continue
                    rows.append([Paragraph(inline(c.strip()),styles['CellCustom'])
                                 for c in line.strip('|').split('|')])
                cols = len(rows[0])
                widths = ([width*.5]+[width*.5/(cols-1)]*(cols-1)) if cols == 3 else [width/cols]*cols
                table = Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf5')),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fb')]),
                    ('VALIGN',(0,0),(-1,-1),'TOP'),
                    ('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),
                    ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#becbd9'))]))
                story.extend([table,Spacer(1,10)])
            else:
                story.append(Paragraph(inline(block.replace('\n',' ')),styles['BodyCustom']))
    doc = SimpleDocTemplate(str(REPORT/'final_report.pdf'),pagesize=A4,
                            rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=48,
                            title='Cloud workload forecasting',author='Candidate submission')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)


if __name__ == '__main__':
    main()
