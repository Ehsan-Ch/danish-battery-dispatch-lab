"""Reproduce dispatch, interval journal, and static report from pinned inputs."""
import csv
import gzip
import hashlib
import io
import json
import platform
from dataclasses import asdict
from pathlib import Path
import numpy as np
import scipy
from .battery import Battery, optimize, idle, settle
from .source import load, SHA256, URL, SELECTED

POLICIES = ('selected', 'weekly', 'idle', 'hindsight')
METRICS = ('gross', 'fee', 'wear', 'net', 'import_mwh', 'export_mwh', 'loss_mwh', 'cycles')

def run(root, out=None):
    root = Path(root); out = Path(out) if out else root/'reports'
    out.mkdir(parents=True, exist_ok=True)
    b = Battery(); days = load(root/'data/forecasts.csv.gz')
    rows = []; daily = []; view = []
    for i, day in enumerate(days):
        record = {k:v for k,v in day.items() if k not in ('selected', 'weekly')}
        record['forecast'] = {k:day[k] for k in ('selected', 'weekly')}
        record['policies'] = {}
        for policy in POLICIES:
            prices = day['actual'] if policy == 'hindsight' else day.get(policy)
            schedule = idle(len(day['utc'])) if policy == 'idle' else optimize(prices, b)
            cash = settle(day['actual'], schedule, b)
            totals = {k:float(cash[k].sum()) for k in METRICS}
            summary = {'area': day['area'], 'day': day['day'], 'policy': policy,
                       **totals, **{f'solver_{k}':v for k,v in schedule['solver'].items()}}
            daily.append(summary)
            record['policies'][policy] = {
                'charge': np.round(schedule['charge'], 7).tolist(),
                'discharge': np.round(schedule['discharge'], 7).tolist(),
                'soc': np.round(schedule['soc'], 7).tolist(),
                'totals': totals, 'solver': schedule['solver']}
            for t, utc in enumerate(day['utc']):
                rows.append({'area': day['area'], 'day': day['day'], 'policy': policy,
                             'issue_utc': day['issue'], 'delivery_utc': utc, 'delivery_local': day['local'][t],
                             'actual_eur_mwh': day['actual'][t],
                             'planning_eur_mwh': '' if policy == 'idle' else prices[t],
                             'charge_mw': schedule['charge'][t], 'discharge_mw': schedule['discharge'][t],
                             'soc_start_mwh': schedule['soc'][t], 'soc_end_mwh': schedule['soc'][t+1],
                             **{k:cash[k][t] for k in METRICS}})
        view.append(record)
        if (i+1)%10 == 0 or i+1 == len(days): print(f'Solved {i+1}/{len(days)} days', flush=True)
    summary = {}
    for area in SELECTED:
        summary[area] = {}
        for policy in POLICIES:
            subset = [r for r in daily if r['area'] == area and r['policy'] == policy]
            summary[area][policy] = {k:sum(r[k] for r in subset) for k in METRICS}
            summary[area][policy].update({'days': len(subset), 'profitable_days': sum(r['net']>1e-6 for r in subset),
                                         'losing_days': sum(r['net'] < -1e-6 for r in subset),
                                         'worst_day_eur': min(r['net'] for r in subset),
                                         'max_solver_gap': max(r['solver_gap'] for r in subset),
                                         'planning_upper_bound': sum(r['solver_upper_bound'] for r in subset)})
    report = {'title': 'Cellar', 'protocol_sha256': hashlib.sha256((root/'docs/PROTOCOL.md').read_bytes()).hexdigest(),
              'source': {'url': URL, 'sha256': SHA256}, 'selected_models': SELECTED, 'battery': asdict(b),
              'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__},
              'summary': summary, 'days': view}
    (out/'results.json').write_text(json.dumps(report, separators=(',', ':'), allow_nan=False), encoding='utf-8')
    buf = io.StringIO(newline=''); writer = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    (out/'dispatch.csv.gz').write_bytes(gzip.compress(buf.getvalue().encode(), mtime=0))
    with (out/'daily.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(daily[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(daily)
    print(json.dumps(summary, indent=2), flush=True)
    return report
