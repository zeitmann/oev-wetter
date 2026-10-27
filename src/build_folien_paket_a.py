"""Folien fuer Paket A (Konzept und Rahmen) erstellen.

Aufbau, Farben und Schrift wie bei den Folien von Paket C (src/build_folien.py).
Optional: pip install python-pptx
Quellen (APA 7):
Canny, S. (2025). python-pptx documentation. https://python-pptx.readthedocs.io/
Inhalte: docs/konzept.md und docs/lifecycle.md.
"""
import unicodedata
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
NAVY = '17364A'
GREEN = '167D8D'
GREY = '53616B'
WHITE = 'FFFFFF'
LIGHT = 'EEF4F6'
FOOTER = 'Gruppe 4 · Timon · Paket A · 27.10.2026 | Quellen: SBB AG (o. J.), Reis & Housley (2022), DuckDB Foundation (2026)'


def out_dir():
    """Ordner docs/praesentation (Umlaut-Schreibweise des Dateisystems egal)."""
    for p in (ROOT / 'docs').iterdir():
        if unicodedata.normalize('NFC', p.name) == 'präsentation':
            return p
    p = ROOT / 'docs' / 'präsentation'
    p.mkdir(parents=True, exist_ok=True)
    return p


def text(slide, x, y, w, h, value, size=20, color=NAVY, bold=False, italic=False, space=12):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate(value.split('\n')):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = line
        p.font.name = 'Aptos'
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.italic = italic
        p.font.color.rgb = RGBColor.from_string(color)
        p.space_after = Pt(space)
    return box


def card(slide, x, y, w, h, fill=WHITE, line=GREEN):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(fill)
    if line:
        shape.line.color.rgb = RGBColor.from_string(line)
        shape.line.width = Pt(1.25)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def base(prs, title, index, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(WHITE)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor.from_string(GREEN)
    bar.line.fill.background()
    if title:
        text(slide, .5, .35, 12.3, .6, title, 30, bold=True)
    text(slide, .5, 7.08, 11.9, .3, FOOTER, 10, GREY)
    text(slide, 12.4, 7.06, .5, .3, str(index), 11, GREY)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def main():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    prs.core_properties.title = 'ÖV und Wetter: Paket A'
    prs.core_properties.author = 'Timon · Gruppe 4'
    prs.core_properties.subject = 'Konzept, Hypothesen, Methodik und Lifecycle'

    # 1 Titel
    s = base(prs, None, 1,
        'Begrüssung, Thema in einem Satz: Wir untersuchen, ob und wie stark Niederschlag, '
        'Schnee und Frost die Pünktlichkeit von Bahn und Bus in der Ostschweiz beeinflussen. '
        'Gesamtdauer des Referats: 15 Minuten, je ca. 5 Minuten pro Person.')
    text(s, .55, 1.5, 12.2, .5, 'PROJEKTARBEIT TEIL 1 · DATA ENGINEERING HS26', 20, GREEN, True)
    text(s, .55, 2.2, 12.2, 2.2, 'Beeinflusst das Wetter die Pünktlichkeit des öV?', 46, NAVY, True)
    text(s, .55, 4.3, 12.2, .6, 'Bahn und Bus in der Ostschweiz, Winter 2026', 26, GREEN, True)
    text(s, .55, 5.2, 12.2, .5, 'Gruppe 4: Timon, Aladin, Enis', 22)
    text(s, .55, 5.8, 12.2, .5, 'Kolloquium 4. November 2026, 18:00 · Raum SW 111', 18, GREY)

    # 2 Ablauf
    s = base(prs, 'Drei Pakete, je ca. 5 Minuten', 2,
        'Ca. 30 Sekunden. Kurz den Ablauf nennen: Jede Person präsentiert einen eigenständigen '
        'Teil. Danach 7 Minuten Diskussion im Plenum.')
    pakete = [('Paket A · Timon', 'Konzept und Rahmen',
               'Problemstellung, Forschungsfrage, Hypothesen, Methodik, Lifecycle'),
              ('Paket B · Aladin', 'Daten rein',
               'Ist-Daten, Ingestion, Storage-Entscheid, Datenmodell'),
              ('Paket C · Enis', 'Daten verknüpfen',
               'Wetterdaten, Bereinigung, Join, Resultate, Limitationen')]
    for i, (who, what, desc) in enumerate(pakete):
        x = .55 + i * 4.15
        card(s, x, 1.5, 3.95, 3.6)
        text(s, x + .25, 1.75, 3.5, .5, who, 20, GREEN, True)
        text(s, x + .25, 2.45, 3.5, .7, what, 26, NAVY, True)
        text(s, x + .25, 3.6, 3.5, 1.4, desc, 19, GREY)
    text(s, .55, 5.6, 12, .5, 'Danach: Fragen und Diskussion im Plenum (7 Minuten)', 22, GREEN, True)

    # 3 Problemstellung
    s = base(prs, 'Problemstellung: Wetter und Pünktlichkeit im öV', 3,
        'Ca. 45 Sekunden. Warum ist das Thema relevant? Drei Nutzergruppen nennen. Die Ostschweiz '
        'mischt Flachland, Voralpen und Hügelland, deshalb ist sie für eine Wetteranalyse '
        'interessant. Das Wetter wirkt je nach Verkehrsmittel und Tageszeit vermutlich unterschiedlich.')
    text(s, .55, 1.3, 12.2, 1.2,
        'Verspätungen kosten Anschlüsse, Geld und Vertrauen. Im Winter kommen Niederschlag, '
        'Schnee und Frost dazu, die niemand steuern, aber berücksichtigen kann.', 23)
    gruppen = [('Pendlerinnen und Pendler', 'Wann ist mit Verspätungen zu rechnen?'),
               ('ÖV-Betreiber', 'Ist Bus oder Bahn stärker betroffen?'),
               ('Planerinnen und Planer', 'Wo lohnen sich Reserven im Fahrplan?')]
    for i, (head, body) in enumerate(gruppen):
        x = .55 + i * 4.15
        card(s, x, 2.7, 3.95, 2.6)
        text(s, x + .25, 2.95, 3.5, .8, head, 22, GREEN, True)
        text(s, x + .25, 3.9, 3.5, 1.3, body, 19)
    text(s, .55, 5.75, 12.2, .8,
        'Untersuchungsgebiet: Thurgau, St. Gallen, Appenzell\nBahn und Bus · 1.1.–31.3.2026',
        20, GREEN, True, space=4)

    # 4 Forschungsfrage und Hypothesen
    s = base(prs, 'Forschungsfrage und Hypothesen', 4,
        'Ca. 60 Sekunden. Forschungsfrage vorlesen, dann die drei Hypothesen. H1 fragt, ob es einen '
        'Effekt gibt, H2 und H3 fragen, ob er je nach Verkehrsmittel und Tageszeit unterschiedlich '
        'stark ist.')
    text(s, .55, 1.3, 12.2, 1.4,
        'Wie stark beeinflusst das Wetter die Pünktlichkeit des öffentlichen Verkehrs in der '
        'Ostschweiz, und unterscheidet sich der Effekt nach Verkehrsmittel und Tageszeit?',
        24, GREEN, True, italic=True)
    hyp = [('H1', 'Bei starkem Niederschlag oder Schnee ist die mittlere Verspätung höher als sonst.'),
           ('H2', 'Der Effekt ist beim Bus stärker als bei der Bahn.'),
           ('H3', 'Der Effekt ist in der Hauptverkehrszeit stärker als ausserhalb.')]
    for i, (nr, body) in enumerate(hyp):
        y = 3.0 + i * 1.25
        card(s, .55, y, 12.2, 1.1, fill=LIGHT, line=None)
        text(s, .8, y + .25, 1.1, .6, nr, 30, GREEN, True)
        text(s, 2.0, y + .18, 10.5, .8, body, 20)

    # 5 Operationalisierung und Methodik
    s = base(prs, 'Operationalisierung und Methodik', 5,
        'Ca. 60 Sekunden. Wie messen wir? Verspätungen sind rechtsschief, deshalb rangbasierte Tests '
        'statt t-Test. Bei Millionen von Halten wird fast alles signifikant, darum immer auch die '
        'Effektstärke. Für H2 und H3 prüfen wir mit einer Wechselwirkung, ob der Effekt je nach '
        'Verkehrsmittel oder Tageszeit unterschiedlich ist. Quelle der 3-Minuten-Schwelle: '
        'SBB AG (o. J.).')
    zeilen = [('Verspätung', 'Ankunft: Ist minus Soll in Minuten, nur gemessene Werte'),
              ('Verspätet', 'ab 3 Minuten (Definition SBB AG, o. J.)'),
              ('Starker Niederschlag', 'Stundensumme über dem 90. Perzentil der Regenstunden'),
              ('Hauptverkehrszeit', 'Mo–Fr, 6–9 und 16–19 Uhr (Lokalzeit)'),
              ('Plausibilität', '−10 bis +60 Minuten, Ausfälle und Durchfahrten ausgeschlossen')]
    for i, (term, desc) in enumerate(zeilen):
        y = 1.35 + i * .82
        text(s, .55, y, 3.9, .6, term, 20, GREEN, True)
        text(s, 4.5, y, 8.3, .6, desc, 20)
    text(s, .55, 5.6, 12.2, 1.1,
        'Tests: H1 Mann-Whitney-U · H2 und H3 Regression mit Wechselwirkung\n'
        'α = 0,05 · Effektstärke immer mit angegeben', 19, GREEN, True, space=4)

    # 6 Lifecycle
    s = base(prs, 'Lifecycle und Unterströmungen', 6,
        'Ca. 90 Sekunden. Der Lifecycle nach den Kursfolien (Reis & Housley). Wir besitzen keine '
        'Quellsysteme, alle Daten sind offene Daten. Ingestion läuft als Batch, weil historische '
        'Archive. Storage ist DuckDB, Begründung im Teil von Aladin. Als Unterströmungen: Security '
        '(nur offene Daten, Rohdaten nur mit ZHAW-Konto), Data Management (Quellenprofile, '
        'Schema-Absprache), DataOps (idempotente Ingestion, Log), Data Architecture (skalierbar, '
        'PostgreSQL als nächste Stufe), Orchestration (manuell, feste Reihenfolge der Skripte), '
        'Software Engineering (Python, SQL, Git). Serving: Web-Dashboard in Teil 2. '
        'Details in docs/lifecycle.md.')
    phasen = [('Generation', 'Ist-Daten v2\nGTFS\nswissBOUNDARIES3D\nMeteoSchweiz', 'umgesetzt'),
              ('Ingestion', 'Python-Skripte, Batch\nÖV: Monats-Zip\nWetter: STAC-CSV\nidempotent', 'umgesetzt'),
              ('Storage', 'DuckDB und Parquet\nDaten auf OneDrive', 'umgesetzt'),
              ('Transformation', 'Bereinigung\nräumlicher und zeitlicher Join\nHypothesentests', 'umgesetzt'),
              ('Serving', 'Web-Dashboard\nKarte, Zeitreihen, Wetterfilter', 'Entwurf für Teil 2')]
    for i, (name, body, status) in enumerate(phasen):
        x = .55 + i * 2.47
        card(s, x, 1.35, 2.35, 3.2)
        text(s, x + .1, 1.5, 2.2, .5, name, 16, GREEN, True)
        text(s, x + .1, 2.05, 2.2, 1.9, body, 13, NAVY, space=5)
        text(s, x + .1, 4.05, 2.2, .4, status, 12, GREY if i == 4 else GREEN, True)
    band = card(s, .55, 4.85, 12.2, 1.0, fill=NAVY, line=None)
    text(s, .8, 5.0, 11.7, .8,
        'Unterströmungen: Security · Data Management · DataOps · Data Architecture · '
        'Orchestration · Software Engineering', 17, WHITE, True)
    text(s, .55, 6.1, 12.2, .6,
        'Stand: Generation bis Transformation sind umgesetzt, Serving ist der Entwurf für Teil 2.',
        16, GREEN, True)

    # 7 Ausblick
    s = base(prs, 'Ausblick: Teil 2', 7,
        'Kurzer Ausblick, ca. 30 Sekunden. Das Ergebnis soll als Web-Dashboard dargestellt werden '
        '(Serving-Option A). Danach Überleitung zur Diskussion.')
    teil2 = [('Transformation', 'Feedback aus Teil 1 einarbeiten, finale Antwort auf die Forschungsfrage'),
             ('Serving', 'Web-Dashboard mit Karte, Zeitreihen und Wetterfiltern'),
             ('Skalierung', 'Mehr Kantone, Deutschschweiz oder ganze Schweiz, falls die Pipeline stabil läuft')]
    for i, (head, body) in enumerate(teil2):
        x = .55 + i * 4.15
        card(s, x, 1.5, 3.95, 3.2)
        text(s, x + .25, 1.75, 3.5, .6, head, 26, GREEN, True)
        text(s, x + .25, 2.6, 3.5, 1.9, body, 20)
    text(s, .55, 5.4, 12.2, .6, 'Abgabe Teil 2: 8. Dezember 2026 · Fragen und Diskussion (7 Minuten)',
         19, GREEN, True)

    # 8 Quellen
    s = base(prs, 'Quellen (Anhang)', 8, 'Anhang, nicht Teil der fünf Minuten. Links sind anklickbar.')
    references = [
        ('SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). Ist-Daten v2 [Datensatz]. Open-Data-Plattform Mobilität Schweiz.',
         'https://archive.opentransportdata.swiss/actual_data_archive.htm'),
        ('SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). Fahrplan 2026 (GTFS) [Datensatz]. Open-Data-Plattform Mobilität Schweiz.',
         'https://archive.opentransportdata.swiss/timetable_gtfs.htm'),
        ('Bundesamt für Landestopografie swisstopo. (2026). swissBOUNDARIES3D [Datensatz].',
         'https://www.swisstopo.admin.ch'),
        ('SBB AG. (o. J.). So misst die SBB die Pünktlichkeit [Webseite].',
         'https://company.sbb.ch/de/unternehmen/verantwortung/kunden/puenktlichkeit.html'),
        ('DuckDB Foundation. (2026). DuckDB documentation.',
         'https://duckdb.org/docs/'),
        ('Reis, J., & Housley, M. (2022). Fundamentals of data engineering. O’Reilly Media.', ''),
        ('Weitere Quellen (MeteoSchweiz, swisstopo Höhendienst, SciPy, statsmodels): siehe Folie Quellen von Paket C und README.', '')]
    for i, (reference, url) in enumerate(references):
        value = reference + ('\n' + url if url else '')
        box = text(s, .55, 1.3 + i * .8, 12.2, .75, value, 14, space=2)
        if url:
            for run in box.text_frame.paragraphs[-1].runs:
                run.hyperlink.address = url

    target = out_dir() / 'folien_paket_a.pptx'
    prs.save(target)
    print(f'{target.name}: {len(prs.slides)} Folien mit Sprechernotizen')


if __name__ == '__main__':
    main()
