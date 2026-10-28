"""Mixed-integer dispatch with independently checked physical accounting."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix

@dataclass(frozen=True)
class Battery:
    power_mw: float = 1.0
    capacity_mwh: float = 2.0
    initial_mwh: float = 1.0
    efficiency_charge: float = .95
    efficiency_discharge: float = .95
    fee_eur_mwh: float = 2.0
    wear_eur_cell_mwh: float = 8.0
    step_hours: float = .25

    def __post_init__(self):
        if not all(np.isfinite(v) for v in asdict(self).values()):
            raise ValueError('Battery parameters must be finite')
        if min(self.power_mw, self.capacity_mwh, self.step_hours) <= 0:
            raise ValueError('Power, capacity and step must be positive')
        if not 0 <= self.initial_mwh <= self.capacity_mwh:
            raise ValueError('Initial state is outside capacity')
        if not all(0 < v <= 1 for v in (self.efficiency_charge, self.efficiency_discharge)):
            raise ValueError('Efficiencies must lie in (0, 1]')
        if min(self.fee_eur_mwh, self.wear_eur_cell_mwh) < 0:
            raise ValueError('Costs must be nonnegative')

def vector(values):
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or not len(a) or not np.isfinite(a).all():
        raise ValueError('Expected a nonempty finite one-dimensional vector')
    return a

def validate(schedule, battery=Battery(), tolerance=1e-6):
    c, d, s = (vector(schedule[k]) for k in ('charge', 'discharge', 'soc'))
    b = battery
    if len(c) != len(d) or len(s) != len(c)+1:
        raise ValueError('Schedule shape mismatch')
    if min(c.min(), d.min(), s.min()) < -tolerance or max(c.max(), d.max()) > b.power_mw+tolerance or s.max() > b.capacity_mwh+tolerance:
        raise ValueError('Physical bound violated')
    if np.minimum(c, d).max() > tolerance:
        raise ValueError('Simultaneous charge/discharge')
    if max(abs(s[0]-b.initial_mwh), abs(s[-1]-b.initial_mwh)) > tolerance:
        raise ValueError('Boundary state mismatch')
    residual = np.diff(s)-b.step_hours*(b.efficiency_charge*c-d/b.efficiency_discharge)
    if np.abs(residual).max() > tolerance:
        raise ValueError('Energy balance violated')

def settle(prices, schedule, battery=Battery()):
    p = vector(prices); validate(schedule, battery)
    c, d = np.asarray(schedule['charge']), np.asarray(schedule['discharge'])
    if len(p) != len(c): raise ValueError('Price/schedule shape mismatch')
    b = battery
    imported, exported = c*b.step_hours, d*b.step_hours
    gross = p*(exported-imported)
    fee = b.fee_eur_mwh*(imported+exported)
    wear = b.wear_eur_cell_mwh*exported/b.efficiency_discharge
    return {'gross': gross, 'fee': fee, 'wear': wear, 'net': gross-fee-wear,
            'import_mwh': imported, 'export_mwh': exported,
            'loss_mwh': imported-exported,
            'cycles': exported/b.efficiency_discharge/b.capacity_mwh}

def idle(n, battery=Battery()):
    if not isinstance(n, int) or n < 1: raise ValueError('Invalid horizon')
    return {'charge': np.zeros(n), 'discharge': np.zeros(n),
            'soc': np.full(n+1, battery.initial_mwh),
            'solver': {'status': 0, 'gap': 0., 'upper_bound': 0., 'objective': 0., 'method': 'idle'}}

def optimize(forecast, battery=Battery()):
    """Accept forecast only. Actual prices enter the separate settle function."""
    p = vector(forecast); n = len(p); b = battery
    # [charge(n), discharge(n), SOC(n+1), mode(n)]
    m = 4*n+1; s0 = 2*n; z0 = 3*n+1
    objective = np.zeros(m)
    objective[:n] = b.step_hours*(p+b.fee_eur_mwh)
    objective[n:2*n] = b.step_hours*(-p+b.fee_eur_mwh+b.wear_eur_cell_mwh/b.efficiency_discharge)
    lo = np.zeros(m); hi = np.ones(m)
    hi[:2*n] = b.power_mw; hi[s0:z0] = b.capacity_mwh
    lo[s0] = hi[s0] = lo[z0-1] = hi[z0-1] = b.initial_mwh
    integrality = np.zeros(m); integrality[z0:] = 1
    A = lil_matrix((3*n, m)); lower = np.full(3*n, -np.inf); upper = np.zeros(3*n)
    for t in range(n):
        A[t, s0+t+1] = 1; A[t, s0+t] = -1
        A[t, t] = -b.efficiency_charge*b.step_hours
        A[t, n+t] = b.step_hours/b.efficiency_discharge
        lower[t] = 0
        A[n+t, t] = 1; A[n+t, z0+t] = -b.power_mw
        A[2*n+t, n+t] = 1; A[2*n+t, z0+t] = b.power_mw
        upper[2*n+t] = b.power_mw
    result = milp(objective, integrality=integrality, bounds=Bounds(lo, hi),
                  constraints=LinearConstraint(A.tocsc(), lower, upper),
                  options={'time_limit': 20., 'mip_rel_gap': 1e-6})
    if result.status != 0 or result.x is None:
        raise RuntimeError(f'Dispatch not optimal: {result.status}: {result.message}')
    schedule = {'charge': result.x[:n], 'discharge': result.x[n:2*n], 'soc': result.x[s0:z0],
                'solver': {'status': int(result.status), 'gap': float(result.mip_gap),
                           'upper_bound': float(-result.mip_dual_bound),
                           'objective': float(-result.fun), 'method': 'HiGHS MILP'}}
    validate(schedule, b)
    if not np.isclose(settle(p, schedule, b)['net'].sum(), -result.fun, atol=1e-5):
        raise RuntimeError('Solver objective failed independent reconciliation')
    return schedule
