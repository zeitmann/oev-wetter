"""Gezielte Kontrollen fuer Intervallgrenzen, Sommerzeit und Effektvorzeichen."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import duckdb
import pandas as pd
from analyse import compare, interaction
from transform import WETTER_STUNDE


class PaketCTest(unittest.TestCase):
    def test_wetter_intervall_und_sommerzeit(self):
        with duckdb.connect() as con:
            con.execute("SET TimeZone='UTC'")
            rows=con.execute(f'''WITH h AS (SELECT unnest([
                '2026-01-10 10:00:00+00'::TIMESTAMPTZ,
                '2026-01-10 10:00:01+00'::TIMESTAMPTZ,
                '2026-03-29 01:30:00+01'::TIMESTAMPTZ,
                '2026-03-29 03:30:00+02'::TIMESTAMPTZ]) AS an_soll)
                SELECT strftime({WETTER_STUNDE},'%H:%M') FROM h''').fetchall()
            self.assertEqual([r[0] for r in rows],['10:00','11:00','01:00','02:00'])
            hours=con.execute("""SELECT date_diff('hour',
                timezone('Europe/Zurich','2026-03-29'::DATE::TIMESTAMP),
                timezone('Europe/Zurich','2026-03-30'::DATE::TIMESTAMP))""").fetchall()[0][0]
            self.assertEqual(hours,23)

    def test_effekt_vorzeichen(self):
        frame=pd.DataFrame({'an_verspaetung_min':[0.,1.,4.,5.],
                            'wetter':[False,False,True,True]})
        result=compare(frame,'wetter','Test')
        self.assertEqual(result['rang_biserial'],1)
        self.assertEqual(result['differenz_min'],4)

    def test_leere_gruppe(self):
        frame=pd.DataFrame({'an_verspaetung_min':[0.], 'wetter':[False]})
        self.assertIn('hinweis',compare(frame,'wetter','Test'))

    def test_interaktion_ist_differenz_der_effekte(self):
        # Bahn: Wettereffekt +1; Bus: Wettereffekt +4 => Interaktion +3.
        frame=pd.DataFrame({'an_verspaetung_min':[0.,.2,1.,1.2,2.,2.2,6.,6.2],
            'starker_niederschlag':[False,False,True,True]*2,
            'bus':[False]*4+[True]*4})
        result=interaction(frame,'bus','H2')
        self.assertAlmostEqual(result['interaktion_min'],3)
        self.assertLess(result['ci95_unten'],3)
        self.assertGreater(result['ci95_oben'],3)


if __name__=='__main__':
    unittest.main()
