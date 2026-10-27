"""Fertige Folien fuer Paket C aus den vorhandenen Ergebnissen erstellen.

Optional: pip install python-pptx
Quellen (APA 7):
Canny, S. (2025). python-pptx documentation. https://python-pptx.readthedocs.io/
Datenquellen und statistische Methoden: docs/quellenprofil_wetter.md und
docs/transformation.md. Quelle Wetterdaten: MeteoSchweiz.
"""
import json
import unicodedata
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/ergebnisse'
NAVY = '17364A'
GREEN = '167D8D'
GREY = '53616B'
WHITE = 'FFFFFF'


def folien_dir():
    """Ordner docs/praesentation (Schreibweise des Umlauts im Dateisystem egal)."""
    for p in (ROOT / 'docs').iterdir():
        if unicodedata.normalize('NFC', p.name) == 'präsentation':
            return p
    p = ROOT / 'docs' / 'präsentation'
    p.mkdir(parents=True, exist_ok=True)
    return p


def text(slide, x, y, w, h, value, size=20, color=NAVY, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate(value.split('\n')):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = line
        p.font.name = 'Aptos'
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = RGBColor.from_string(color)
        p.space_after = Pt(12)
    return box


def base(prs, title, index, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string(WHITE)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = RGBColor.from_string(GREEN)
    bar.line.fill.background()
    text(slide, .5, .35, 12.3, .6, title, 30, bold=True)
    text(slide, .5, 7.08, 11.9, .3,
         'Gruppe 4 · Enis · Paket C · 27.10.2026 | Quellen: MeteoSchweiz (2026), SBB/SKI (2026), swisstopo (2026)',
         10, GREY)
    text(slide, 12.4, 7.06, .5, .3, str(index), 11, GREY)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def main():
    params = json.loads((OUT / 'parameter.json').read_text(encoding='utf-8'))
    tests = pd.read_csv(OUT / 'hypothesentests.csv').set_index('vergleich')
    reg = pd.read_csv(OUT / 'regression.csv').set_index('hypothese')
    h1 = tests.loc['H1: starker Niederschlag']
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    prs.core_properties.title = 'ÖV und Wetter: Paket C'
    prs.core_properties.author = 'Enis · Gruppe 4'
    prs.core_properties.subject = 'Wetterdaten, Bereinigung, Join und Hypothesen H1–H3'

    s = base(prs, 'Wetterdaten passend zu jedem Halt', 1,
        'Ca. 50 Sekunden. Wir übernehmen die Ist-Daten und das Schema von Paket B. '
        'MeteoSchweiz wurde gegenüber Open-Meteo gewählt, weil Stationsmessungen zum '
        'geplanten Stationsmodell passen. Fertige Stundenwerte statt eigener Aggregation. '
        'Die Wetterzeit ist das Intervallende: 10:30 UTC wird 11:00 UTC zugeordnet; '
        'genau 10:00 UTC bleibt 10:00 UTC. Beide Quellen werden in UTC verbunden, '
        'Tageszeit und Wochentag aus Europe/Zurich abgeleitet.')
    text(s, .55, 1.35, 5.9, .6, '13 Stationen · 10 geeignet', 29, GREEN, True)
    text(s, .55, 2.2, 5.8, 3.9,
        'MeteoSchweiz SwissMetNet, Januar–März 2026\n'
        'Stundenwerte: Niederschlag und Temperatur; Wind und Schnee soweit verfügbar\n'
        'QUI, SCM und STK fehlen die Kernparameter', 23)
    text(s, 7, 1.35, 5.7, .6, '2’540 Haltestellen zugeordnet', 27, GREEN, True)
    text(s, 7, 2.2, 5.7, 3.9,
        'Nächste geeignete Station: höchstens 30 km und 500 m Höhenunterschied\n'
        'Geländehöhen mit swisstopo ergänzt; 47 Haltestellen ohne passende Station\n'
        'Join nach Soll-Ankunft und Wetterintervall in UTC', 23)
    text(s, .55, 6.2, 12, .5, 'Bestehende Basis: Python + DuckDB + Parquet', 22, GREEN, True)

    s = base(prs, 'Bereinigung: von 17,07 auf 11,63 Mio. Halte', 2,
        'Ca. 55 Sekunden. EDA vor Bereinigung nach Verkehrsmittel, Kanton und Tageszeit. '
        'Zuerst fehlende Ankünfte, dann nicht gemessene Werte, Ausfälle, Durchfahrten '
        'und unplausible Verspätungen ausschliessen. Die Bilanz zählt jeden Halt einmal. '
        'Nach Bereinigung bleiben 11.671.172 Halte; 44.243 verlieren wir mangels geeigneter '
        'Station. Final 11.626.929. Die REAL-Anteile beziehen sich auf den Ankunftsstatus '
        'aller Rohhalte, einschliesslich Halten ohne Soll-Ankunft, nicht auf Bs Abfahrtsquoten.')
    text(s, .55, 1.4, 4.5, 3.7,
        'Nur gemessene Ankünfte (REAL)\nKeine Ausfälle oder Durchfahrten\n'
        'Plausibilität: −10 bis +60 Minuten\nVerspätet: mindestens 3 Minuten', 22)
    s.shapes.add_picture(str(OUT / 'verspaetungsverteilung.png'), Inches(5.05), Inches(1.4), width=Inches(7.85))
    text(s, .55, 5.7, 12, .9,
        'Ankunftsstatus REAL vor Bereinigung: Bahn 89,72 % · Bus 65,94 %\n'
        'Unterschiedliche Messabdeckung bleibt eine Grenze des Vergleichs.', 20, GREY)

    s = base(prs, 'H1: Bei starkem Niederschlag etwas mehr Verspätung', 3,
        'Ca. 75 Sekunden. Stark bedeutet strikt mehr als 1,7 mm pro Stunde. Das ist das '
        '90. Perzentil positiver Stationsstunden, vor dem Halt-Join berechnet. '
        'Vergleich stark gegen alle übrigen Halte: 1,613 statt 1,393 Minuten. '
        'Mann-Whitney-U prüft Verteilungsunterschiede; ergänzend Mittelwertdifferenz. '
        'Rang-biserial r=0,070, p<0,001: kleiner Zusammenhang. '
        'Die Grafik zeigt drei Wetterklassen, der Test vergleicht stark gegen trocken und mässig zusammen. '
        'H2: Bus +0,212 und Bahn +0,214 Minuten. Interaktion −0,0017 Minuten, '
        '95%-KI [−0,0299; 0,0264], p=0,904. H2 wird absolut nicht gestützt. Relativ ist es eher umgekehrt: '
        'Der Anteil verspäteter Halte steigt bei der Bahn von 5,5 auf 8,0 % (+45 %), beim Bus von 13,4 auf '
        '16,5 % (+23 %), und r ist bei der Bahn grösser (0,103 statt 0,063). Die Mittelwerte steigen '
        'abgestuft von trocken über mässig zu stark, das stützt H1 zusätzlich.')
    text(s, .55, 1.3, 12.2, .75,
        f'+{h1.differenz_min*60:.1f} Sekunden im Mittel · {h1.verspaetet_sonst_anteil*100:.2f} % → '
        f'{h1.verspaetet_wetter_anteil*100:.2f} % verspätete Halte'.replace('.', ','), 27, GREEN, True)
    s.shapes.add_picture(str(OUT / 'wetter_verkehrsmittel.png'), Inches(.5), Inches(2.45), width=Inches(8.8))
    text(s, 9.55, 2.4, 3.25, 3.8,
        f'Stark: > {params["niederschlag_q90_mm"]:.1f} mm/h\n'.replace('.', ',') +
        'Kleiner Effekt: r = 0,070\np < 0,001\n'
        'H2 nicht gestützt: absolut gleicher Effekt (+0,21 Min.), relativ bei der Bahn eher stärker', 18)
    text(s, .55, 6.45, 12, .35, 'Abgestuft trocken → mässig → stark: Bus 1,45 → 1,61 → 1,69 Min. · Bahn 0,83 → 1,04 → 1,07 Min. '
         '(H1-Test: stark gegen sonst)', 15, GREY)

    s = base(prs, 'H3: Die Hauptverkehrszeit verstärkt den Effekt nicht', 4,
        'Ca. 60 Sekunden. HVZ Montag bis Freitag, 6 bis 9 und 16 bis 19 Uhr lokal, '
        'gesetzliche kantonale Feiertage ausgenommen. Während der HVZ ist das '
        'allgemeine Verspätungsniveau höher. Das ist aber etwas anderes als die '
        'Verstärkung des Wettereffekts: HVZ +0,208 gegenüber NVZ +0,268 Minuten. '
        'OLS-Interaktion −0,0603 Minuten, 95%-KI [−0,0816; −0,0389], p<0,001. '
        'Die Richtung ist umgekehrt, die Differenz etwa 3,6 Sekunden. '
        'Die Regression nutzt alle bereinigten Halte, ohne Stichprobe. Relativ: Anteil verspäteter Halte '
        'HVZ 19,2 → 22,9 % (+20 %), NVZ 9,5 → 13,1 % (+38 %).')
    s.shapes.add_picture(str(OUT / 'wetter_hvz.png'), Inches(.55), Inches(1.4), width=Inches(8.35))
    text(s, 9.15, 1.65, 3.6, 3.8,
        'Wettereffekt stark vs. sonst:\nHVZ: +0,208 Minuten\nNVZ: +0,268 Minuten\n'
        f'Interaktion: {reg.loc["H3", "interaktion_min"]:.3f} Minuten\nH3 nicht gestützt'.replace('.', ','), 22)
    text(s, .55, 6.4, 12, .4, 'Höheres Verspätungsniveau in der HVZ ≠ stärkerer Wettereffekt.', 21, GREEN, True)

    s = base(prs, 'Ein kleiner Zusammenhang – mit klaren Grenzen', 5,
        'Ca. 60 Sekunden. Insgesamt hängt starker Niederschlag in diesem Winterquartal '
        'mit etwas höheren Ankunftsverspätungen zusammen. Kein stärkerer Effekt beim '
        'Bus oder in der HVZ. Keine Kausalität: Baustellen, Störungen und Nachfrage '
        'sind nicht kontrolliert. Halte derselben Fahrt sind abhängig; klassische '
        'p-Werte und Konfidenzintervalle können zu optimistisch sein. '
        'Schnee ergänzend nur +0,029 Minuten, r=0,014. Je nach Station wird Schneedecke '
        'oder Niederschlag bei Frost beobachtet, kein einheitlicher Schneefall. '
        'Die 47 Haltestellen ohne geeignete Station liegen alle auf rund 1000 m oder höher, also dort, '
        'wo Schnee am wichtigsten wäre. Ausgefallene Fahrten können wetterbedingt sein; weil sie '
        'ausgeschlossen sind, wird der Effekt eher unterschätzt (Ausfallquote nach Wetter für Teil 2). '
        'Die bereinigten Halte und eine Stundenaggregation stehen für Teil 2 bereit.')
    text(s, .55, 1.4, 5.9, 3.7,
        'Beobachteter Zusammenhang, keine Kausalität\n'
        'Nur ein Winterquartal; weitere Ursachen fehlen\n'
        'Halte derselben Fahrt sind nicht unabhängig\n'
        'Ausfälle ausgeschlossen: Effekt eher unterschätzt', 21)
    text(s, 7, 1.4, 5.75, 3.7,
        'Wetterstation liegt nicht direkt am Halt\n'
        'Unterschiedliche REAL-Abdeckung bei Bahn und Bus\n'
        'Schneedecke und Frostniederschlag sind keine einheitliche Schneefallmessung\n'
        '47 Haltestellen ab ca. 1000 m ohne Station, gerade dort zählt Schnee', 21)
    text(s, .55, 5.8, 12, .9,
        'Für Teil 2 vorbereitet: bereinigte Halte + Stundenaggregation\n'
        'Nachvollziehbar in ausgeführten Notebooks und DuckDB/Parquet.', 23, GREEN, True)

    s = base(prs, 'Quellen (Anhang)', 6, 'Anhang, nicht Teil der fünf Minuten. Vollständige Links sind anklickbar.')
    references = [
        ('Bundesamt für Meteorologie und Klimatologie MeteoSchweiz. (2026). Automatische Wetterstationen: Messwerte [Datensatz]. Quelle: MeteoSchweiz.',
         'https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn'),
        ('SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). Ist-Daten v2 [Datensatz]. Open-Data-Plattform Mobilität Schweiz.',
         'https://archive.opentransportdata.swiss/actual_data_archive.htm'),
        ('Bundesamt für Landestopografie swisstopo. (2026). Height: GeoAdmin API [Höhendienst].',
         'https://api3.geo.admin.ch/services/sdiservices.html#height'),
        ('The SciPy community. (2026). scipy.stats.mannwhitneyu. Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference.',
         'https://www.statsmodels.org/stable/regression.html')]
    for i, (reference, url) in enumerate(references):
        box = text(s, .55, 1.35+i*1.28, 12.2, 1.1, reference+'\n'+url, 16)
        for run in box.text_frame.paragraphs[-1].runs:
            run.hyperlink.address = url
    target = folien_dir() / 'folien_paket_c.pptx'
    prs.save(target)
    print(f'{target.name}: {len(prs.slides)} Folien mit Sprechernotizen')


if __name__ == '__main__':
    main()
