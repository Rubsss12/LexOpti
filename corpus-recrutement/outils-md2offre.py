# -*- coding: utf-8 -*-
"""Convertit les offres d'emploi texte du corpus en PDF."""
import os, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                HRFlowable)

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "offres")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "offres-pdf")
os.makedirs(OUT, exist_ok=True)

INK  = colors.HexColor("#1a1a1a")
GREY = colors.HexColor("#6b6b6b")
RULE = colors.HexColor("#c8c8c8")

ST = dict(
    title=ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=18, leading=22,
                         textColor=INK, spaceAfter=3),
    entity=ParagraphStyle("e", fontName="Helvetica-Bold", fontSize=9.5, leading=13,
                          textColor=INK),
    meta=ParagraphStyle("m", fontName="Helvetica", fontSize=8.5, leading=12,
                        textColor=GREY),
    head=ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                        textColor=GREY, spaceBefore=15, spaceAfter=3),
    body=ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=14,
                        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=6),
    note=ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=7, leading=9,
                        textColor=GREY),
)

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def is_head(s):
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters) and len(s) < 45

def build(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    note = ""
    if lines and lines[-1].startswith("FICHE FICTIVE"):
        note = lines[-1].strip()
        lines = lines[:-1]
    title, entity, meta = lines[0].strip(), lines[1].strip(), lines[2].strip()

    story = [Paragraph(esc(title), ST["title"]),
             Paragraph(esc(entity), ST["entity"]),
             Paragraph(esc(meta), ST["meta"]),
             Spacer(1, 6),
             HRFlowable(width="100%", thickness=0.7, color=RULE, spaceAfter=2)]

    prose, prev = [], 0

    def flush():
        if prose:
            story.append(Paragraph(esc(" ".join(prose)), ST["body"]))
            prose.clear()

    for ln in lines[3:]:
        s = ln.strip()
        if not s:
            flush()
        elif is_head(s):
            flush()
            story.append(Paragraph(esc(s), ST["head"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=RULE,
                                    spaceBefore=0, spaceAfter=5))
        else:
            if prose and prev < 70:      # ligne isolee, pas un retour a la ligne
                flush()
            prose.append(s)
        prev = len(s)
    flush()

    if note:
        story.append(Spacer(1, 7))
        story.append(Paragraph(esc(note), ST["note"]))

    out = os.path.join(OUT, os.path.basename(path).replace(".md", ".pdf"))
    SimpleDocTemplate(out, pagesize=A4,
                      leftMargin=22*mm, rightMargin=22*mm,
                      topMargin=20*mm, bottomMargin=16*mm,
                      title=title, author="HUB Institute",
                      subject="Offre fictive - corpus de test").build(story)
    return out

made = [build(p) for p in sorted(glob.glob(os.path.join(SRC, "*.md")))]
print("%d offres generees" % len(made))
