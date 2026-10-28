"""Hash-pinned forecast import, preserving local days and UTC interval keys."""
import csv
import gzip
import hashlib
import io
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import math

SHA256 = '11dc413033af9ddfda6e16b2b9d1a2a067ad6482e186453282d6c1f38625937c'
COMMIT = 'a8244399f0886d07ddafbe1d71b757abcb97ae95'
URL = f'https://raw.githubusercontent.com/Ehsan-Ch/danish-power-forecast-lab/{COMMIT}/reports/benchmark/predictions.csv.gz'
SELECTED = {'DK1': 'ridge', 'DK2': 'boosted'}
DK = ZoneInfo('Europe/Copenhagen')
UTC = timezone.utc

def stamp(t): return t.astimezone(UTC).isoformat().replace('+00:00', 'Z')
def parse(t):
    d = datetime.fromisoformat(t.replace('Z', '+00:00'))
    if d.tzinfo is None: raise ValueError('Timestamp needs an offset')
    return d.astimezone(UTC)
def slots(day):
    d = date.fromisoformat(day)
    start = datetime.combine(d, datetime.min.time(), DK).astimezone(UTC)
    end = datetime.combine(d+timedelta(days=1), datetime.min.time(), DK).astimezone(UTC)
    return [stamp(start+timedelta(minutes=15*i)) for i in range(int((end-start).total_seconds()/900))]
def issue(day):
    return stamp((datetime.fromisoformat(day).replace(tzinfo=DK)-timedelta(days=1)).replace(hour=10))

def load(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256: raise ValueError('Forecast archive hash mismatch')
    groups = {}
    for r in csv.DictReader(io.StringIO(gzip.decompress(raw).decode())):
        if r['partition'] != 'test': continue
        area = r['area']; model = r['model']
        if area not in SELECTED: raise ValueError('Unknown area')
        if model not in ('weekly', SELECTED[area]): continue
        day = parse(r['delivery_utc']).astimezone(DK).date().isoformat()
        if not '2026-07-01' <= day <= '2026-09-30': raise ValueError('Unexpected evaluation date')
        if r['issue_utc'] != issue(day): raise ValueError('Unexpected decision cutoff')
        if parse(r['delivery_local']) != parse(r['delivery_utc']): raise ValueError('Local/UTC mismatch')
        if not all(math.isfinite(float(r[k])) for k in ('actual', 'forecast')): raise ValueError('Nonfinite price')
        key = (area, day); g = groups.setdefault(key, {})
        bucket = g.setdefault(model, {})
        if r['delivery_utc'] in bucket: raise ValueError('Duplicate prediction')
        bucket[r['delivery_utc']] = r
    expected = [(a, (date(2026,7,1)+timedelta(days=i)).isoformat()) for a in SELECTED for i in range(92)]
    if set(groups) != set(expected): raise ValueError('Missing evaluation days')
    days = []
    for area, day in expected:
        keys = slots(day); g = groups[(area, day)]
        if set(g) != {'weekly', SELECTED[area]} or any(set(rows) != set(keys) for rows in g.values()):
            raise ValueError('Incomplete delivery day')
        selected = [g[SELECTED[area]][t] for t in keys]; weekly = [g['weekly'][t] for t in keys]
        if any(float(s['actual']) != float(w['actual']) for s,w in zip(selected, weekly)):
            raise ValueError('Actual prices disagree across models')
        days.append({'area': area, 'day': day, 'issue': issue(day), 'utc': keys,
                     'local': [parse(t).astimezone(DK).isoformat() for t in keys],
                     'actual': [float(r['actual']) for r in selected],
                     'selected': [float(r['forecast']) for r in selected],
                     'weekly': [float(r['forecast']) for r in weekly]})
    return days
