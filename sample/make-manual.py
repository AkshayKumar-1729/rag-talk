"""
Renders sample/aeronote-manual.md to sample/aeronote-manual.pdf — the PDF
rag-build.ipynb downloads and parses.

The styling is lifted from the film (rag-pipeline.html, buildPage()): a cobalt
masthead, two columns, bordered figures with mono captions, teal specification
tables, and a footer carrying "Aeronote Ltd · confidential" and a folio. That
isn't decoration — the film's narration says parsing is "where the columns, the
header, the page number and the table stop existing", and this is the document
that makes that literally true for the notebook's §2/§3.

Section 2.3 "The reading surface" is a deliberate reproduction of the page the
film draws, down to the tablet-and-stylus figure and the three-row spec table.

    python sample/make-manual.py
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

MANUAL_MD = Path(__file__).parent / "aeronote-manual.md"
OUT_PDF = Path(__file__).parent / "aeronote-manual.pdf"

# ------------------------------------------------------- palette, from the film
COBALT = colors.HexColor("#2F6BFF")
COBALT_INK = colors.HexColor("#1A4ED8")
COBALT_SOFT = colors.HexColor("#E4ECFF")
FIG_BORDER = colors.HexColor("#C9DAFF")
FIG_BG = colors.HexColor("#F5F8FF")
TEAL = colors.HexColor("#0E9C8B")
TEAL_SOFT = colors.HexColor("#DBF3EF")
TEAL_LINE = colors.HexColor("#9FD9D0")
RULE = colors.HexColor("#D6DEE6")
INK = colors.HexColor("#2b3a47")
INK_FAINT = colors.HexColor("#8A98A6")
SCREEN_TINT = colors.HexColor("#DBF3EF")
SCREEN_EDGE = colors.HexColor("#8FCFC6")

PAGE_W, PAGE_H = 5.5 * inch, 8.5 * inch  # half-letter: a real manual booklet
MARGIN = 0.42 * inch
MAST_H = 0.30 * inch
FOOT_H = 0.34 * inch
COL_GAP = 0.20 * inch

MASTHEAD_LEFT = "AERONOTE — USER MANUAL"
FOOTER_LEFT = "Aeronote Ltd · confidential"

# The masthead's right-hand side names the chapter and the section currently on
# the page — the same "Ch. 2 · The display" shape the film's masthead uses, and a
# normal running-head convention. It's drawn in onPageEnd, after the page's
# content has been laid out, so it names what is actually on the page.

# ------------------------------------------------------------------------ styles
body_style = ParagraphStyle(
    "Body", fontName="Helvetica", fontSize=8.2, leading=12.4, textColor=INK,
    spaceAfter=7, alignment=0,
)
h2_style = ParagraphStyle(
    "H2", fontName="Helvetica-Bold", fontSize=9.6, leading=12.5,
    textColor=COBALT_INK, spaceBefore=8, spaceAfter=4,
)
figcap_style = ParagraphStyle(
    "FigCap", fontName="Courier", fontSize=5.8, leading=8, textColor=COBALT_INK,
    alignment=TA_CENTER, spaceBefore=3, spaceAfter=7,
)
title_style = ParagraphStyle(
    "Title", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=COBALT_INK,
    spaceAfter=5,
)
subtitle_style = ParagraphStyle(
    "Subtitle", fontName="Courier", fontSize=7.4, leading=11, textColor=INK_FAINT,
    spaceAfter=16,
)
chapter_style = ParagraphStyle(
    "Chapter", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
    textColor=COBALT_INK, spaceBefore=2, spaceAfter=8,
)


# ----------------------------------------------------------------------- figures
class TabletFigure(Flowable):
    """The film's fig. 2.1 — tablet, tinted screen with text lines, stylus, and the
    ambient light the reading-surface section is about. Traced from the SVG in
    rag-pipeline.html buildPage()."""

    def __init__(self, width, height=64):
        Flowable.__init__(self)
        self.width, self.height = width, height

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        c.setFillColor(FIG_BG)
        c.setStrokeColor(FIG_BORDER)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, w, h, 4, stroke=1, fill=1)

        # the film's viewBox is 104x38; centre that inside our box
        s = min(w / 118.0, h / 46.0)
        ox, oy = (w - 104 * s) / 2, (h - 38 * s) / 2

        def X(v):
            return ox + v * s

        def Y(v):  # SVG y is top-down, PDF is bottom-up
            return oy + (38 - v) * s

        c.setStrokeColor(COBALT)
        c.setLineWidth(1.1 * s)
        c.setFillColor(colors.white)
        c.roundRect(X(13), Y(36), 62 * s, 34 * s, 3 * s, stroke=1, fill=1)

        c.setFillColor(SCREEN_TINT)
        c.setStrokeColor(SCREEN_EDGE)
        c.setLineWidth(0.6 * s)
        c.roundRect(X(17), Y(32), 54 * s, 26 * s, 1.4 * s, stroke=1, fill=1)

        for y, wdt, col in [
            (10, 30, TEAL), (15, 44, SCREEN_EDGE),
            (20, 38, SCREEN_EDGE), (25, 26, colors.HexColor("#B9E1DB")),
        ]:
            c.setFillColor(col)
            c.roundRect(X(21), Y(y + 2), wdt * s, 2 * s, 1 * s, stroke=0, fill=1)

        c.setFillColor(COBALT)
        c.roundRect(X(79), Y(32), 3.4 * s, 26 * s, 1.7 * s, stroke=0, fill=1)

        c.setStrokeColor(COBALT)
        c.setLineWidth(1.1 * s)
        c.setLineCap(1)
        for x1, y1, x2, y2 in [(92, 9, 98, 12), (92, 19, 99, 19), (92, 29, 98, 26)]:
            c.line(X(x1), Y(y1), X(x2), Y(y2))


class SimpleFigure(Flowable):
    """A light generic figure box for the other illustrated pages — a framed panel
    with a few abstract elements, enough to be furniture the parser must skip."""

    def __init__(self, width, height=54, kind="pages"):
        Flowable.__init__(self)
        self.width, self.height, self.kind = width, height, kind

    def draw(self):
        c = self.canv
        w, h = self.width, self.height
        c.setFillColor(FIG_BG)
        c.setStrokeColor(FIG_BORDER)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, w, h, 4, stroke=1, fill=1)
        cx, cy = w / 2, h / 2

        if self.kind == "pages":  # three offset page cards
            for i, dx in enumerate([-20, -4, 12]):
                c.setFillColor(colors.white if i < 2 else COBALT_SOFT)
                c.setStrokeColor(COBALT if i == 2 else FIG_BORDER)
                c.setLineWidth(0.7)
                c.roundRect(cx + dx - 9, cy - 15, 18, 30, 2, stroke=1, fill=1)
            c.setFillColor(TEAL)
            for j in range(3):
                c.roundRect(cx + 6, cy + 6 - j * 6, 12, 1.6, 0.8, stroke=0, fill=1)
        elif self.kind == "cloud":  # device syncing upward
            c.setStrokeColor(COBALT)
            c.setLineWidth(1.1)
            c.setFillColor(colors.white)
            c.roundRect(cx - 30, cy - 14, 22, 28, 2.5, stroke=1, fill=1)
            c.setFillColor(COBALT_SOFT)
            c.setStrokeColor(COBALT)
            c.roundRect(cx + 6, cy - 6, 30, 16, 7, stroke=1, fill=1)
            c.setStrokeColor(TEAL)
            c.setLineWidth(1.2)
            c.setLineCap(1)
            c.line(cx - 4, cy + 2, cx + 2, cy + 2)
            c.line(cx - 1, cy + 5, cx + 2, cy + 2)
            c.line(cx - 1, cy - 1, cx + 2, cy + 2)
        else:  # "stylus" — nib on a ruled surface
            c.setStrokeColor(SCREEN_EDGE)
            c.setLineWidth(0.6)
            for j in range(4):
                c.line(cx - 34, cy - 12 + j * 8, cx + 12, cy - 12 + j * 8)
            c.setFillColor(COBALT)
            c.setStrokeColor(COBALT)
            c.setLineWidth(1.1)
            c.line(cx + 6, cy + 16, cx + 26, cy - 10)
            c.circle(cx + 27, cy - 12, 2.2, stroke=0, fill=1)


def spec_table(rows, width):
    data = [["Specification", "Value"]] + rows
    t = Table(data, colWidths=[width * 0.56, width * 0.44], hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Courier-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 5.6),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 6.4),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#26433f")),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.6, TEAL_LINE),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#CFE9E4")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, TEAL_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), TEAL_SOFT))
    t.setStyle(TableStyle(style))
    return t


# Which sections get a figure and/or a table, and what they say.
# 2.3 is the film's page, reproduced.
FIGURES = {
    "2.3": ("tablet", "fig. 2.1 — the reading surface"),
    "4.2": ("pages", "fig. 4.1 — page templates"),
    "5.2": ("cloud", "fig. 5.1 — sync and export"),
    "2.5": ("stylus", "fig. 2.2 — the stylus nib"),
}
TABLES = {
    "2.3": [["Screen", "10.3-inch e-ink"], ["Weight", "375 g"], ["Charge", "3 weeks"]],
    "13.1": [["Display", "10.3-inch, 300 ppi"], ["Body", "195 × 145 × 4.6 mm"],
             ["Mass", "375 g"], ["Storage", "32 GB"]],
}


# ------------------------------------------------------------- page furniture
class ManualDoc(BaseDocTemplate):
    """Tracks which chapter/section each page belongs to so the masthead can name
    it. Markers are zero-height flowables, so `afterFlowable` sees them as the page
    is laid out and the furniture (drawn in onPageEnd) reads the right values."""

    def __init__(self, *args, **kwargs):
        BaseDocTemplate.__init__(self, *args, **kwargs)
        self.current_chapter = "1"
        self.current_section = "About Aeronote"

    def afterFlowable(self, flowable):
        marker = getattr(flowable, "_marker", None)
        if not marker:
            return
        kind, value = marker
        if kind == "chapter":
            self.current_chapter = value
        else:
            self.current_section = value


def draw_furniture(canvas, doc):
    canvas.saveState()

    # masthead: cobalt bar bleeding to both edges
    canvas.setFillColor(COBALT)
    canvas.rect(0, PAGE_H - MAST_H, PAGE_W, MAST_H, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Courier-Bold", 5.6)
    canvas.drawString(MARGIN, PAGE_H - MAST_H + 0.105 * inch, MASTHEAD_LEFT)
    ch = getattr(doc, "current_chapter", "1")
    sec = getattr(doc, "current_section", "")
    right = f"CH. {ch} · {sec.upper()}"
    canvas.setFillColor(colors.HexColor("#B9D0FF"))
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MAST_H + 0.105 * inch, right)

    # footer: hairline, imprint left, folio right
    y = FOOT_H
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, y + 0.13 * inch, PAGE_W - MARGIN, y + 0.13 * inch)
    canvas.setFont("Courier", 5.8)
    canvas.setFillColor(INK_FAINT)
    canvas.drawString(MARGIN, y, FOOTER_LEFT)
    canvas.setFont("Courier-Bold", 6.6)
    canvas.setFillColor(COBALT_INK)
    canvas.drawRightString(PAGE_W - MARGIN, y, str(doc.page))

    canvas.restoreState()


class Marker(Spacer):
    """Zero-height flowable whose only job is to tell the doc which chapter or
    section we're in, so the masthead on this page names it."""

    def __init__(self, kind, value):
        Spacer.__init__(self, 1, 0)
        self._marker = (kind, value)


# ------------------------------------------------------------------ the content
def esc(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def build_story(markdown_text, col_width):
    story = []
    lines = markdown_text.splitlines()
    i, first_chapter = 0, True
    pending = []  # body paragraph lines for the section being read
    current_section = None

    def flush_section():
        """Emit the section that was being accumulated, with its figure/table."""
        nonlocal pending, current_section
        if current_section is None:
            pending = []
            return
        num, title = current_section
        head = [
            Marker("section", title),
            Paragraph(
                f'<font face="Courier-Bold" size="7.4" color="#2F6BFF">{num}</font>'
                f'&nbsp;&nbsp;{esc(title)}', h2_style),
        ]
        if num in FIGURES:
            kind, caption = FIGURES[num]
            fig = TabletFigure(col_width) if kind == "tablet" else SimpleFigure(col_width, kind=kind)
            head += [fig, Paragraph(caption, figcap_style)]
        # heading, figure and caption must never be split across a column break
        story.append(KeepTogether(head))
        text = " ".join(pending).strip()
        if text:
            story.append(Paragraph(esc(text), body_style))
        if num in TABLES:
            story.extend([Spacer(1, 2), KeepTogether(spec_table(TABLES[num], col_width)), Spacer(1, 8)])
        pending, current_section = [], None

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("# "):
            story.append(Paragraph(esc(line[2:]), title_style))
        elif line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            story.append(Paragraph(esc(line.strip("*")), subtitle_style))
        elif line.startswith("## "):
            flush_section()
            heading = line[3:]
            num = heading.split(".")[0].strip()
            if not first_chapter:
                story.append(PageBreak())
            first_chapter = False
            story.append(Marker("chapter", num))
            story.append(Paragraph(esc(heading), chapter_style))
        elif line.startswith("### "):
            flush_section()
            m = re.match(r"(\d+\.\d+)\s+(.+)", line[4:])
            current_section = (m.group(1), m.group(2)) if m else (None, line[4:])
        elif line.strip():
            pending.append(line.strip())
        i += 1

    flush_section()
    return story


def main():
    markdown_text = MANUAL_MD.read_text(encoding="utf-8")

    usable_w = PAGE_W - 2 * MARGIN
    col_w = (usable_w - COL_GAP) / 2
    frame_bottom = FOOT_H + 0.20 * inch
    frame_top = PAGE_H - MAST_H - 0.16 * inch
    frame_h = frame_top - frame_bottom

    frames = [
        Frame(MARGIN, frame_bottom, col_w, frame_h, id="left",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
        Frame(MARGIN + col_w + COL_GAP, frame_bottom, col_w, frame_h, id="right",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
    ]

    doc = ManualDoc(
        str(OUT_PDF), pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MAST_H, bottomMargin=FOOT_H,
        title="Aeronote — Product Guide & Policies", author="Aeronote Ltd",
    )
    doc.addPageTemplates([
        PageTemplate(id="two-col", frames=frames, onPageEnd=draw_furniture)
    ])
    doc.build(build_story(markdown_text, col_w))
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
