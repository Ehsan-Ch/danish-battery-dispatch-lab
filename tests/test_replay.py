import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from cellar.source import load, slots, issue
from cellar.battery import validate, settle

ROOT = Path(__file__).resolve().parents[1]

class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load(ROOT/'data/forecasts.csv.gz')
        cls.report = json.loads((ROOT/'reports/results.json').read_text())

    def test_archive_has_all_evaluation_days(self):
        self.assertEqual(len(self.source),184)
        self.assertTrue(all(len(d['utc'])==96 for d in self.source))

    def test_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.gz'; p.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'hash mismatch'): load(p)

    def test_dst_day_lengths_and_unique_keys(self):
        for day,n in [('2025-10-26',100),('2026-03-29',92),('2026-07-01',96)]:
            s=slots(day); self.assertEqual(len(s),n); self.assertEqual(len(set(s)),n)
        self.assertEqual(issue('2026-07-01'),'2026-06-30T08:00:00Z')
        self.assertEqual(issue('2026-01-01'),'2025-12-31T09:00:00Z')

    def test_protocol_hash(self):
        self.assertEqual(self.report['protocol_sha256'], hashlib.sha256((ROOT/'docs/PROTOCOL.md').read_bytes()).hexdigest())

    def test_all_schedules_feasible_and_totals_reconcile(self):
        for day in self.report['days']:
            for policy,s in day['policies'].items():
                validate(s)
                totals=settle(day['actual'],s)
                for k,v in totals.items():
                    self.assertAlmostEqual(float(sum(v)),s['totals'][k],delta=.002)
                self.assertEqual(s['solver']['status'],0)
                self.assertLessEqual(s['solver']['gap'],1.0001e-6)
            oracle=day['policies']['hindsight']
            for policy,s in day['policies'].items():
                self.assertLessEqual(s['totals']['net'],oracle['solver']['upper_bound']+1e-4)

    def test_summary_is_daily_sum(self):
        for area, policies in self.report['summary'].items():
            for policy, summary in policies.items():
                days=[d['policies'][policy] for d in self.report['days'] if d['area']==area]
                self.assertEqual(summary['days'],92)
                for k in ('net','gross','fee','wear','loss_mwh','cycles'):
                    self.assertAlmostEqual(sum(d['totals'][k] for d in days),summary[k],places=6)
                self.assertGreaterEqual(summary['loss_mwh'],-1e-5)

    def test_full_precision_journal(self):
        with gzip.open(ROOT/'reports/dispatch.csv.gz','rt') as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),184*4*96)
        self.assertEqual(len({(r['area'],r['policy'],r['delivery_utc']) for r in rows}),len(rows))
        for r in rows:
            c,d=float(r['charge_mw']),float(r['discharge_mw'])
            self.assertAlmostEqual(float(r['soc_end_mwh'])-float(r['soc_start_mwh']),.25*(.95*c-d/.95),places=6)
            self.assertAlmostEqual(float(r['gross'])-float(r['fee'])-float(r['wear']),float(r['net']),places=7)
        for area in ('DK1','DK2'):
            actual=sum(float(r['net']) for r in rows if r['area']==area and r['policy']=='selected')
            self.assertAlmostEqual(actual,self.report['summary'][area]['selected']['net'],places=5)

    def test_reports_keep_original_forecasts(self):
        for raw,view in zip(self.source,self.report['days']):
            self.assertEqual(raw['actual'],view['actual'])
            self.assertEqual(raw['selected'],view['forecast']['selected'])
            self.assertEqual(raw['weekly'],view['forecast']['weekly'])

if __name__ == '__main__': unittest.main()
