"""H1-H3 nach Paket A auswerten und Grafiken fuer Notebook/Folien speichern.

Quellen (APA 7):
Wallroth, T. (2026). Konzeptionalisierung (AP 2). docs/konzept.md (Projektintern).
The SciPy community. (2026). scipy.stats.mannwhitneyu.
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical
modeling with Python. Proceedings of the 9th Python in Science Conference.
https://www.statsmodels.org/stable/regression.html
"""
import argparse
import gc
import os
from pathlib import Path

# Projektordner; Matplotlib-Cache nach data/raw legen, damit nichts im Repo landet.
ROOT=Path(__file__).resolve().parent.parent
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data/raw/.cache/matplotlib'))

import duckdb
import matplotlib
# Grafiken ohne Bildschirm erzeugen (Skript laeuft auch ohne GUI).
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
import statsmodels.api as sm

# Ergebnisse (CSV und PNG) landen in docs/ergebnisse und sind im Repo.
OUT=ROOT/'docs/ergebnisse'


def compare(frame, flag, label, selection=None):
    """Zweiseitiger Test; positive Effektstaerke = mehr Verspaetung bei Wetter."""
    if selection is not None:
        frame=frame.loc[selection]
    # Halte ohne Wert fuer diese Wettervariable auslassen.
    frame=frame.loc[frame[flag].notna()]
    # Zwei Gruppen: Halte mit Wetterereignis (wet) und alle uebrigen Halte (other).
    wet=frame.loc[frame[flag], 'an_verspaetung_min'].to_numpy()
    other=frame.loc[~frame[flag], 'an_verspaetung_min'].to_numpy()
    # Ohne beide Gruppen ist kein Test moeglich (z. B. bei einem kurzen Testzeitraum).
    if len(wet)==0 or len(other)==0:
        return {'vergleich':label,'n_wetter':len(wet),'n_sonst':len(other),
                'hinweis':'Nicht auswertbar: eine Gruppe ist leer'}
    # Mann-Whitney-U (rangbasiert, weil Verspaetungen schief verteilt sind), zweiseitig.
    # Ausgegeben werden Mittel, Median, Anteil verspaeteter Halte (>= 3 Min.), U, p-Wert
    # und als Effektstaerke die rang-biseriale Korrelation r = 2U/(n1*n2) - 1.
    result=mannwhitneyu(wet,other,alternative='two-sided',method='asymptotic')
    return {'vergleich':label,'n_wetter':len(wet),'n_sonst':len(other),
            'mittel_wetter_min':wet.mean(),'mittel_sonst_min':other.mean(),
            'differenz_min':wet.mean()-other.mean(),
            'median_wetter_min':np.median(wet),'median_sonst_min':np.median(other),
            'verspaetet_wetter_anteil':np.mean(wet>=3),'verspaetet_sonst_anteil':np.mean(other>=3),
            'u':result.statistic,'p_wert':result.pvalue,
            'rang_biserial':2*result.statistic/(len(wet)*len(other))-1}


def interaction(frame, group, label):
    """OLS auf allen Halten: y = b0 + b1*Wetter + b2*Gruppe + b3*Wetter*Gruppe.

    Zwei Binaervariablen ergeben vier Gruppen. Der Interaktionskoeffizient
    ist die Differenz der beiden Wettereffekte. Keine Stichprobe.
    Klassische Standardfehler; Abhaengigkeit der Halte bleibt eine Limitation.
    """
    # Designmatrix: Konstante, Wetter, Gruppe (Bus bzw. HVZ) und Wetter x Gruppe.
    weather=frame.starker_niederschlag.to_numpy(dtype=float)
    g=frame[group].to_numpy(dtype=float)
    x=np.column_stack((np.ones(len(frame)),weather,g,weather*g))
    # Pruefen, dass alle vier Kombinationen vorkommen, sonst ist die Interaktion nicht schaetzbar.
    if np.linalg.matrix_rank(x.T@x)<4:
        raise ValueError(f'{label}: nicht alle vier Gruppen vorhanden')
    # Lineare Regression; b3 (Index 3) ist der Unterschied des Wettereffekts zwischen den Gruppen.
    model=sm.OLS(frame.an_verspaetung_min.to_numpy(),x).fit()
    ci=model.conf_int()[3]
    row={'hypothese':label,'gruppe':group,'n':int(model.nobs),
         'interaktion_min':float(model.params[3]),'ci95_unten':float(ci[0]),
         'ci95_oben':float(ci[1]),'p_wert':float(model.pvalues[3]),
         'r_quadrat':float(model.rsquared)}
    # Grosse Arrays sofort freigeben (11,6 Mio. Zeilen).
    del model,x,weather,g
    gc.collect()
    return row


# Grafiken fuer Notebook und Folien aus den CSV-Ergebnissen von transform.py.
def plots():
    plt.rcParams.update({'font.size':10,'figure.dpi':130})
    # 1) Verteilung der Ankunftsverspaetung pro Verkehrsmittel (Anteil der Halte pro Minute).
    frame=pd.read_csv(OUT/'verspaetungsverteilung.csv')
    fig,ax=plt.subplots(figsize=(8,4))
    for name,part in frame.groupby('verkehrsmittel_gruppe'):
        ax.plot(part.minute,part.halte/part.halte.sum()*100,label=name)
    ax.set(xlim=(-5,20),xlabel='Ankunftsverspaetung (Minuten)',ylabel='Anteil der Halte (%)')
    ax.legend(); fig.tight_layout(); fig.savefig(OUT/'verspaetungsverteilung.png'); plt.close(fig)
    # 2) Mittlere Verspaetung und Anteil verspaeteter Halte nach Niederschlagsklasse, Bahn vs. Bus (H1/H2).
    groups=pd.read_csv(OUT/'gruppen_verkehrsmittel_gruppe.csv')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,value,ylabel in zip(axes,['mittel_min','verspaetet_anteil'],['Mittlere Verspaetung (Min.)','Verspaetete Halte (Anteil)']):
        groups.pivot(index='verkehrsmittel_gruppe',columns='niederschlagsklasse',values=value).reindex(
            columns=['trocken','maessig','stark']).plot.bar(ax=ax,rot=0)
        ax.set(xlabel='',ylabel=ylabel); ax.legend(title='Niederschlag')
    fig.tight_layout(); fig.savefig(OUT/'wetter_verkehrsmittel.png'); plt.close(fig)
    # 3) Mittlere Verspaetung nach Niederschlagsklasse, Haupt- vs. Nebenverkehrszeit (H3).
    groups=pd.read_csv(OUT/'gruppen_hvz.csv')
    fig,ax=plt.subplots(figsize=(7,4))
    groups['tageszeit']=groups.hvz.map({True:'Hauptverkehrszeit',False:'Nebenverkehrszeit'})
    groups.pivot(index='tageszeit',columns='niederschlagsklasse',values='mittel_min').reindex(
        columns=['trocken','maessig','stark']).plot.bar(ax=ax,rot=0)
    ax.set(xlabel='',ylabel='Mittlere Verspaetung (Min.)'); ax.legend(title='Niederschlag')
    fig.tight_layout(); fig.savefig(OUT/'wetter_hvz.png'); plt.close(fig)
    # 4) Zeitreihe der mittleren Verspaetung pro Betriebstag.
    series=pd.read_csv(OUT/'zeitreihe.csv',parse_dates=['betriebstag'])
    fig,ax=plt.subplots(figsize=(9,4))
    for name,part in series.groupby('verkehrsmittel_gruppe'):
        ax.plot(part.betriebstag,part.mittel_min,label=name)
    ax.set(ylabel='Mittlere Verspaetung (Min.)',xlabel='Betriebstag'); ax.legend()
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(OUT/'zeitreihe.png'); plt.close(fig)


# Hauptablauf: Analysetabelle lesen, Tests H1-H3 rechnen, Ergebnisse und Grafiken speichern.
def analyse(db):
    OUT.mkdir(parents=True,exist_ok=True)
    # Nur die fuer die Tests noetigen Spalten lesen (spart Speicher); Datenbank nur lesend oeffnen.
    with duckdb.connect(str(db),read_only=True) as con:
        frame=con.execute('''SELECT an_verspaetung_min,starker_niederschlag,schnee_frost,
            verkehrsmittel_gruppe='Bus' AS bus,hvz FROM analyse_halt''').df()
    if frame.empty:
        raise ValueError('analyse_halt ist leer: zuerst transform.py ausfuehren')
    # H1: starker Niederschlag gegen alle uebrigen Halte; ergaenzend Schnee/Frost.
    results=[compare(frame,'starker_niederschlag','H1: starker Niederschlag'),
             compare(frame,'schnee_frost','Ergaenzung: Schneedecke / Frostniederschlag')]
    # H1 getrennt nach Bahn/Bus (H2) und HVZ/NVZ (H3), um die Effekte pro Gruppe zu vergleichen.
    for column,labels in [('bus',{True:'Bus',False:'Bahn'}),('hvz',{True:'HVZ',False:'NVZ'})]:
        for value,label in labels.items():
            results.append(compare(frame,'starker_niederschlag',label,frame[column]==value))
    # Ergebnisse der Gruppenvergleiche speichern.
    tests=pd.DataFrame(results)
    tests.to_csv(OUT/'hypothesentests.csv',index=False)
    # H2 und H3 formal: Interaktion in der Regression mit 95%-Konfidenzintervall.
    regression=pd.DataFrame([interaction(frame,'bus','H2'),interaction(frame,'hvz','H3')])
    regression.to_csv(OUT/'regression.csv',index=False)
    del frame
    gc.collect()
    plots()
    print(tests[['vergleich','differenz_min','rang_biserial','p_wert']].to_string(index=False))
    print(regression.to_string(index=False))
    return tests,regression


def main():
    # Kommandozeile: Pfad zur DuckDB-Datei (Standard data/oev_wetter.duckdb).
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',type=Path,default=ROOT/'data/oev_wetter.duckdb')
    analyse(p.parse_args().db)


if __name__=='__main__':
    main()
