# Results and limitations

Base asset: 1 MW / 2 MWh. Period: 1 July–30 September 2026, 92 days per area. All values below are hypothetical operating cash flows in EUR, after the frozen fee and wear assumptions.

| Area / policy | Gross | Fee | Wear | Net | Cell cycles | Energy lost MWh |
|---|---:|---:|---:|---:|---:|---:|
| DK1 frozen forecast | 25,208.07 | 988.51 | 1,974.43 | 22,245.12 | 123.40 | 25.33 |
| DK1 weekly forecast | 26,304.31 | 1,246.30 | 2,489.32 | 22,568.69 | 155.58 | 31.94 |
| DK1 hindsight | 31,940.29 | 1,239.12 | 2,474.98 | 28,226.19 | 154.69 | 31.75 |
| DK2 frozen forecast | 23,646.16 | 925.98 | 1,849.52 | 20,870.67 | 115.60 | 23.73 |
| DK2 weekly forecast | 26,651.89 | 1,242.31 | 2,481.36 | 22,928.22 | 155.08 | 31.83 |
| DK2 hindsight | 31,580.25 | 1,237.65 | 2,472.04 | 27,870.57 | 154.50 | 31.71 |

Idle has zero energy movement, costs, cycles and cash flow. The frozen forecast's net cash flow trails weekly by €323.56 in DK1 and €2,057.56 in DK2. Its gap to perfect-price hindsight is €5,981.07 and €6,999.90 respectively. Model selection by price MAE in the earlier benchmark does not optimize battery value; trading intensity, price ranking and spread timing matter too. These results do not isolate a causal reason for the difference.

All three active policies have positive modeled daily net cash flow on all 92 days in both areas. The frozen forecast's worst days are €27.29 (DK1) and €24.86 (DK2). This favorable sample is not evidence of risk-free future revenue. It omits several real-world costs and risks and spans only one summer quarter.

All 552 MILP solves returned status 0. Maximum reported relative gap was 3.36e−16; every schedule passes independent physical checks. There are 736 policy-day records including idle, and 70,656 quarter-hour records. Initial and final cell energy equal 1 MWh on every day. Total import minus export reconciles to physical losses over each daily cycle.

## What limits the conclusion

- The period was already examined in prior projects. Battery parameters were frozen before this replay, but this is an extension of familiar data, not fresh prospective evidence.
- Hindsight sees actual target-day prices. It is a reference bound, not an executable early forecast policy.
- Schedules are committed before assumed price knowledge, then filled at clearing prices. No bid acceptance, partial fills, slippage or imbalance settlement is modeled.
- No capital cost, financing, taxes, grid tariffs, capacity charges, self-discharge, ramp rates or reserve obligations.
- Flat wear cost per cell-discharge MWh is a proxy; battery aging depends on temperature, state, depth and power.
- Daily terminal SOC prevents free energy but also restricts cross-day optimization. No claim is made that this is an economically optimal operating horizon.
- Uniform asset scaling in the UI preserves duration and all linear assumptions. It is not a separately optimized asset-sizing or investment study.

Useful extensions: an unseen year, authentic publication-time data, bid/settlement rules, realistic tariff and aging models, and a separate decision-focused forecast selection period. None are represented as completed here.
