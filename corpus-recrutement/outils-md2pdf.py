# -*- coding: utf-8 -*-
"""Convertit les CV texte du corpus en PDF avec une mise en page de CV."""
import os, re, glob
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                HRFlowable, ListFlowable, ListItem)

SRC = "/home/user/LexOpti/corpus-recrutement/cv"
OUT = "/home/user/LexOpti/corpus-recrutement/cv-pdf"
os.makedirs(OUT, exist_ok=True)

INK   = colors.HexColor("#1a1a1a")
GREY  = colors.HexColor("#6b6b6b")
RULE  = colors.HexColor("#c8c8c8")

def styles(plain=False):
    """plain=True : rendu volontairement brut, pour le CV mal mis en forme."""
    base = "Helvetica"
    if plain:
        return dict(
            name=ParagraphStyle("n", fontName=base, fontSize=11, leading=15, textColor=INK),
            contact=ParagraphStyle("c", fontName=base, fontSize=11, leading=15, textColor=INK),
            title=ParagraphStyle("t", fontName=base, fontSize=11, leading=15, textColor=INK),
            head=ParagraphStyle("h", fontName=base, fontSize=11, leading=15, textColor=INK,
                                spaceBefore=10),
            job=ParagraphStyle("j", fontName=base, fontSize=11, leading=15, textColor=INK,
                               spaceBefore=6),
            body=ParagraphStyle("b", fontName=base, fontSize=11, leading=15, textColor=INK),
            bullet=ParagraphStyle("u", fontName=base, fontSize=11, leading=15, textColor=INK),
            note=ParagraphStyle("z", fontName=base, fontSize=7, leading=9, textColor=GREY),
        )
    return dict(
        name=ParagraphStyle("n", fontName="Helvetica-Bold", fontSize=19, leading=23,
                            textColor=INK, spaceAfter=2),
        contact=ParagraphStyle("c", fontName="Helvetica", fontSize=8.5, leading=12,
                               textColor=GREY),
        title=ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=10, leading=13,
                             textColor=INK, spaceBefore=8, spaceAfter=2),
        head=ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                            textColor=GREY, spaceBefore=14, spaceAfter=3),
        job=ParagraphStyle("j", fontName="Helvetica-Bold", fontSize=9.5, leading=13,
                           textColor=INK, spaceBefore=8, spaceAfter=1),
        body=ParagraphStyle("b", fontName="Helvetica", fontSize=9.5, leading=13.5,
                            textColor=INK, alignment=TA_JUSTIFY, spaceAfter=2),
        bullet=ParagraphStyle("u", fontName="Helvetica", fontSize=9.5, leading=13.5,
                              textColor=INK),
        note=ParagraphStyle("z", fontName="Helvetica-Oblique", fontSize=7, leading=9,
                            textColor=GREY),
    )

HEADINGS = {"EXPERIENCE", "EXPÉRIENCE", "FORMATION", "COMPETENCES", "COMPÉTENCES",
            "LANGUES", "DIVERS", "CERTIFICATIONS", "NOTE", "NOTE DE CANDIDATURE",
            "NOTE DE MOTIVATION", "CENTRES D'INTERET", "CENTRES D'INTÉRÊT",
            "PARCOURS", "PROFIL"}

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def is_heading(line):
    s = line.strip()
    if not s or s.startswith("-") or "|" in s:
        return False
    if s.upper() in HEADINGS:
        return True
    letters = [c for c in s if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters) and len(s) < 40

def parse(path):
    raw = open(path, encoding="utf-8").read().splitlines()
    note = ""
    if raw and raw[0].startswith("CV FICTIF"):
        note = raw[0].strip()
        raw = raw[1:]
    # recolle les lignes de continuation indentees
    lines, buf = [], None
    for ln in raw:
        if ln.startswith("  ") and ln.strip() and buf is not None:
            buf += " " + ln.strip()
        else:
            if buf is not None:
                lines.append(buf)
            buf = ln.rstrip()
    if buf is not None:
        lines.append(buf)
    while lines and not lines[0].strip():
        lines.pop(0)
    return note, lines

def build(path):
    note, lines = parse(path)
    plain = "aicha-diallo" in path          # CV volontairement mal mis en forme
    st = styles(plain)
    name = lines[0].strip()
    i = 1
    contact = []
    while i < len(lines) and lines[i].strip():
        contact.append(lines[i].strip())
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1

    story = [Paragraph(esc(name), st["name"])]
    if contact:
        sep = "  \u00b7  " if not plain else " "
        story.append(Paragraph(sep.join(esc(c) for c in contact), st["contact"]))
    if not plain:
        story.append(Spacer(1, 5))
        story.append(HRFlowable(width="100%", thickness=0.7, color=RULE,
                                spaceBefore=0, spaceAfter=2))

    # accroche : premiere ligne apres le bloc contact, sauf en rendu brut
    if i < len(lines) and not plain and lines[i].strip().upper() not in HEADINGS:
        story.append(Paragraph(esc(lines[i].strip()), st["title"]))
        i += 1

    bullets, prose = [], []
    prev_len = 0   # longueur de la ligne source precedente

    def flush():
        if prose:
            story.append(Paragraph(esc(" ".join(prose)), st["body"]))
            prose.clear()
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(esc(b), st["bullet"]), leftIndent=10)
                 for b in bullets],
                bulletType="bullet", bulletChar="\u2022", bulletFontSize=7,
                leftIndent=9, bulletOffsetY=-1.5, spaceBefore=1, spaceAfter=1))
            bullets.clear()

    for ln in lines[i:]:
        s = ln.strip()
        if not s:
            flush()
        elif s.startswith("- "):
            if prose:
                story.append(Paragraph(esc(" ".join(prose)), st["body"]))
                prose.clear()
            bullets.append(s[2:])
        elif is_heading(s):
            flush()
            story.append(Paragraph(esc(s), st["head"]))
            if not plain:
                story.append(HRFlowable(width="100%", thickness=0.5, color=RULE,
                                        spaceBefore=0, spaceAfter=4))
        elif "|" in s and not plain:
            flush()
            role, _, dates = s.rpartition("|")
            story.append(Paragraph(
                '%s<font color="#6b6b6b" size="8.5">&nbsp;&nbsp;%s</font>'
                % (esc(role.strip()), esc(dates.strip())), st["job"]))
        else:
            if prose and prev_len < 70:      # ligne volontairement isolee, pas un retour a la ligne
                story.append(Paragraph(esc(" ".join(prose)), st["body"]))
                prose.clear()
            prose.append(s)
        prev_len = len(s)
    flush()

    if note:
        story.append(Spacer(1, 14))
        story.append(Paragraph(esc(note), st["note"]))

    out = os.path.join(OUT, os.path.basename(path).replace(".md", ".pdf"))
    SimpleDocTemplate(out, pagesize=A4,
                      leftMargin=20*mm, rightMargin=20*mm,
                      topMargin=18*mm, bottomMargin=16*mm,
                      title=name, author=name,
                      subject="CV fictif - corpus de test").build(story)
    return out

made = [build(p) for p in sorted(glob.glob(os.path.join(SRC, "*.md")))]
print("%d PDF generes" % len(made))
