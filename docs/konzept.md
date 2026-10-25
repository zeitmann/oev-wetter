# Konzeptionalisierung (AP 2)

Projektarbeit Teil 1, Gruppe 4. Autor: Timon (Paket A). Stand: 25.10.2026

## 1. Problemstellung und Ausgangslage

Der öffentliche Verkehr ist nur dann ein verlässliches Angebot, wenn Fahrgäste sich auf die Fahrpläne verlassen können. Verspätungen führen zu verpassten Anschlüssen, Mehrkosten im Betrieb und sinkender Zufriedenheit. Im Winter kommen Niederschlag, Schnee und Frost als Einflussfaktoren dazu, die Betreiber und Planer kaum steuern, aber berücksichtigen können.

Die Ostschweiz (Thurgau, St. Gallen, Appenzell Ausserrhoden und Innerrhoden) verbindet Flachland, Voralpen und Hügelland mit Bahn- und Busnetz. Diese Mischung macht sie für eine Wetteranalyse interessant. Das Wetter wirkt je nach Verkehrsmittel und Tageszeit vermutlich unterschiedlich.

Nutzen des Ergebnisses:

- **Pendlerinnen und Pendler:** Sie erkennen, bei welchem Wetter und zu welcher Zeit mit Verspätungen zu rechnen ist.
- **ÖV-Betreiber:** Sie sehen, ob Bus oder Bahn stärker betroffen ist und wo Reserven im Fahrplan sinnvoll sind.
- **Planerinnen und Planer:** Sie erhalten eine Datengrundlage für Fahrplan- und Ressourcenentscheide.

## 2. Forschungsfrage

> Wie stark beeinflusst das Wetter die Pünktlichkeit des öffentlichen Verkehrs in der Ostschweiz, und unterscheidet sich der Effekt nach Verkehrsmittel (Bahn/Bus) und Tageszeit?

## 3. Hypothesen

| Nr. | Hypothese |
| --- | --- |
| H1 | Bei starkem Niederschlag oder Schnee ist die mittlere Verspätung höher als sonst. |
| H2 | Der Effekt von H1 ist beim Bus stärker als bei der Bahn. |
| H3 | Der Effekt von H1 ist in der Hauptverkehrszeit stärker als ausserhalb. |

## 4. Operationalisierung

| Begriff | Festlegung |
| --- | --- |
| Verspätung | Ankunftsverspätung pro Halt = Ist-Ankunft minus Soll-Ankunft in Minuten. Es zählen nur Halte mit Ankunft und gemessenem Ist-Wert (`an_status = 'REAL'`, nicht geschätzt oder prognostiziert). Ausgefallene Fahrten (`faellt_aus`) und Durchfahrten werden ausgeschlossen. Plausibilitätsfenster: −10 bis +60 Minuten. Werte ausserhalb (z. B. um einen Tag verschobene Ist-Zeiten) werden entfernt, ihre Anzahl wird in der EDA dokumentiert. Der Anteil gemessener Werte wird in der EDA geprüft und dokumentiert. |
| Verspätet (binär) | Verspätung ≥ 3 Minuten. Schwelle nach SBB AG (o. J.): Ein Zug gilt als pünktlich, wenn er mit weniger als 3 Minuten Verspätung eintrifft. Die SBB zählt ausgefallene Züge als unpünktlich; hier werden sie ausgeschlossen. Die Definition gilt bei der SBB für Züge und wird auf Busse übertragen. |
| Starker Niederschlag | Stundensumme über dem 90. Perzentil aller Stunden mit Niederschlag > 0 mm. Das Quantil wird einmal über den gesamten Zeitraum und alle Stationen berechnet und im Notebook ausgewiesen. |
| Schnee / Frost | Zusätzliche Variable: Niederschlag > 0 mm und Temperatur < 0 °C. Liefert eine Station einen Schneeparameter, hat dieser Vorrang. |
| Hauptverkehrszeit (HVZ) | Montag bis Freitag, 6–9 Uhr und 16–19 Uhr Lokalzeit, Feiertage ausgenommen. Alles andere gilt als Nebenverkehrszeit. |
| Verkehrsmittel | Bahn und Bus, wie in den Ist-Daten klassifiziert. |
| Zeitzone | Lokalzeit mit Zeitzone (ISO 8601). Die Sommerzeitumstellung am 29.3.2026 liegt im Zeitraum und wird in der Bereinigung berücksichtigt. |

## 5. Methodik pro Hypothese

Verspätungen sind rechtsschief und enthalten viele Nullen. Deshalb kommen rangbasierte Verfahren statt t-Test zum Einsatz. Signifikanzniveau: α = 0,05. Bei grossen Datenmengen wird fast alles signifikant, darum wird die Effektstärke immer mit angegeben und zur Interpretation herangezogen.

| Hypothese | Test | Effektstärke |
| --- | --- | --- |
| H1 | Mann-Whitney-U-Test: Verspätung bei starkem Niederschlag vs. sonst. Ergänzend Vergleich des Anteils verspäteter Halte (≥ 3 Min.). | Rang-biseriale Korrelation oder Cliff's Delta; Differenz der Mittelwerte in Minuten |
| H2 | H1 getrennt für Bus und Bahn rechnen und die Effektstärken vergleichen. Ergänzend lineare Regression mit Wechselwirkung Niederschlag × Verkehrsmittel. | Koeffizient der Wechselwirkung mit Konfidenzintervall |
| H3 | Wie H2, mit Wechselwirkung Niederschlag × Hauptverkehrszeit. | Koeffizient der Wechselwirkung mit Konfidenzintervall |

Weitere Festlegungen:

- Schnee/Frost wird im selben Vorgehen wie H1 als zusätzliche Variable ausgewertet, nicht als eigene Hypothese.
- Die Auswertung erfolgt auf Halt-Ebene. Die Abhängigkeit von Halten derselben Fahrt oder Linie wird als Limitation genannt. Falls Zeit bleibt, prüft Paket C eine Aggregation pro Stunde und Linie als Kontrolle.

## 6. Limitationen

- **Räumliche Zuordnung:** Die Wetterstation liegt nicht am Halt. Das Wetter am Halt kann vom Wetter an der Station abweichen, besonders bei Höhenunterschieden.
- **Mehrere Ursachen:** Verspätungen haben viele Ursachen (Baustellen, Störungen, Fahrgastaufkommen). Der Wettereffekt kann nicht isoliert werden. Die Ergebnisse zeigen Zusammenhänge, keine Kausalität.
- **Echtzeitdaten:** Nicht alle Halte haben gemessene Ist-Werte. Fahrten ohne Echtzeitdaten und ausgefallene Fahrten fehlen oder werden gesondert behandelt.
- **Unterschiedliche Datenqualität:** Der Anteil gemessener Werte (`REAL`) ist bei der Bahn deutlich höher als beim Bus (Ankunft am 15.1.2026: Bahn 98 %, Bus 66 %; Abfahrt gesamter Zeitraum: Bahn 97 %, Bus 69 %, siehe `docs/quellenprofil_istdaten.md`). Der Vergleich in H2 beruht deshalb auf unterschiedlich vollständigen Teilmengen.
- **Übertragung der SBB-Definition:** Die 3-Minuten-Schwelle stammt aus der Zugpünktlichkeit und wird für Busse übernommen.
- **Abhängigkeit der Beobachtungen:** Halte derselben Fahrt oder Linie sind nicht unabhängig, was Signifikanzwerte beeinflusst.
- **Zeitraum:** Der Zeitraum umfasst nur drei Monate eines einzigen Winters (1.1.–31.3.2026). Aussagen über andere Jahreszeiten oder Jahre sind nicht möglich.
- **Schwellenwerte:** Die Schwellen (3 Min., 90. Perzentil, HVZ-Fenster) sind Festlegungen. Andere Wahlen können die Ergebnisse verändern.

## 7. Folienvorlage (3–4 Folien)

**Folie 1: Problemstellung**

- ÖV-Pünktlichkeit ist entscheidend für Fahrgäste, Betreiber und Planung
- Ostschweiz (TG, SG, AR, AI): Flachland, Voralpen, Bahn und Bus
- Wetter als Einflussfaktor im Winter

**Folie 2: Forschungsfrage und Hypothesen**

- Forschungsfrage (Zitat aus Abschnitt 2)
- H1, H2, H3 (Tabelle aus Abschnitt 3)

**Folie 3: Operationalisierung und Methodik**

- Tabelle Begriffe (Abschnitt 4), gekürzt auf Verspätung, starker Niederschlag, HVZ
- Tabelle Tests und Effektstärke (Abschnitt 5)
- Hinweis: α = 0,05, Effektstärke wegen grosser Datenmenge

**Folie 4: Limitationen**

- Station nicht am Halt, mehrere Ursachen, fehlende Echtzeitwerte, ein Winter
- Ausblick: Skalierung auf weitere Kantone, Deutschschweiz, ganze Schweiz

## 8. Quellen

SBB AG. (o. J.). *So misst die SBB die Pünktlichkeit* [Webseite]. https://company.sbb.ch/de/unternehmen/verantwortung/kunden/puenktlichkeit.html
