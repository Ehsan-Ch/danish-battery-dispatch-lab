import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
from cellar.battery import Battery, optimize, settle, validate, idle

class PhysicsTests(unittest.TestCase):
    def test_flat_positive_prices_make_idle_optimal(self):
        s = optimize([80.]*8)
        self.assertAlmostEqual(settle([80.]*8, s)['net'].sum(), 0, places=6)
        self.assertLess(np.sum(s['charge']), 1e-6)

    def test_two_interval_analytic_solution(self):
        b = Battery(power_mw=1, capacity_mwh=1, initial_mwh=0, efficiency_charge=1,
                    efficiency_discharge=1, fee_eur_mwh=0, wear_eur_cell_mwh=0, step_hours=1)
        s = optimize([10,100], b)
        np.testing.assert_allclose(s['charge'], [1,0], atol=1e-6)
        np.testing.assert_allclose(s['discharge'], [0,1], atol=1e-6)
        self.assertAlmostEqual(settle([10,100], s, b)['net'].sum(), 90)

    def test_loss_fee_wear_accounting_by_hand(self):
        b = Battery(initial_mwh=0, efficiency_charge=.8, efficiency_discharge=.5, step_hours=1)
        s = {'charge': [1,0], 'discharge': [0,.4], 'soc': [0,.8,0]}
        r = settle([10,100], s, b)
        self.assertAlmostEqual(sum(r['gross']), 30)
        self.assertAlmostEqual(sum(r['fee']), 2.8)
        self.assertAlmostEqual(sum(r['wear']), 6.4)
        self.assertAlmostEqual(sum(r['net']), 20.8)
        self.assertAlmostEqual(sum(r['loss_mwh']), .6)
        self.assertAlmostEqual(sum(r['cycles']), .4)

    def test_negative_prices_never_allow_simultaneous_operations(self):
        s = optimize([-500.,-400.,-300.,-200.]*4)
        validate(s)
        self.assertLess(np.max(np.minimum(s['charge'],s['discharge'])), 1e-6)
        self.assertAlmostEqual(s['soc'][0], s['soc'][-1])

    def test_one_negative_interval_cannot_dissipate_free_energy(self):
        s = optimize([-1000.])
        self.assertAlmostEqual(s['charge'][0], 0)
        self.assertAlmostEqual(s['discharge'][0], 0)

    def test_hindsight_dominates_fixed_schedule(self):
        prices = [120,50,-20,40,160,10,90,60]
        ordinary = optimize(list(reversed(prices)))
        hindsight = optimize(prices)
        self.assertGreaterEqual(sum(settle(prices,hindsight)['net'])+1e-5, sum(settle(prices,ordinary)['net']))

    def test_settlement_does_not_change_decisions(self):
        s = optimize([20,100,10,180]); before = s['charge'].copy()
        one = settle([10,90,20,150], s); two = settle([200,30,150,10], s)
        np.testing.assert_array_equal(s['charge'], before)
        self.assertNotEqual(sum(one['net']),sum(two['net']))

    def test_invalid_inputs(self):
        for p in ([], [float('nan')], [float('inf')], [[1,2]]):
            with self.subTest(p=p), self.assertRaises(ValueError): optimize(p)
        for kw in ({'power_mw':0},{'efficiency_charge':1.1},{'initial_mwh':3},{'fee_eur_mwh':-1}):
            with self.subTest(kw=kw), self.assertRaises(ValueError): Battery(**kw)

    def test_rejects_corrupt_schedules(self):
        for s in ({'charge':[1], 'discharge':[1], 'soc':[1,1]},
                  {'charge':[0], 'discharge':[0], 'soc':[1,1.1]},
                  {'charge':[0,0], 'discharge':[0], 'soc':[1,1]}):
            with self.subTest(s=s), self.assertRaises(ValueError): validate(s)

    def test_solver_timeout_is_not_success(self):
        with patch('cellar.battery.milp', return_value=SimpleNamespace(status=1,x=None,message='limit')):
            with self.assertRaisesRegex(RuntimeError, 'not optimal'): optimize([1,2])

    def test_scaled_asset_preserves_economics(self):
        p = [10,100,10,100]; s = optimize(p)
        b = Battery(power_mw=2,capacity_mwh=4,initial_mwh=2)
        big = optimize(p,b)
        self.assertAlmostEqual(sum(settle(p,big,b)['net']),2*sum(settle(p,s)['net']),places=5)

    def test_idle_zero_accounting(self):
        r = settle([-500,1000], idle(2))
        for values in r.values(): self.assertEqual(sum(values),0)

if __name__ == '__main__': unittest.main()
