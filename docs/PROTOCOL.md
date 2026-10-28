# Cellar: frozen dispatch experiment

Written 27 October 2026 before running the battery experiment. This is a retrospective extension of Nordcast, not a new or unseen forecast benchmark. The July–September sample was already examined in earlier projects. Battery parameters and policies below are fixed before calculating battery results; none are chosen by profit on this sample.

## Inputs and decision

Use the exact Nordcast v1 predictions archive at commit a8244399f0886d07ddafbe1d71b757abcb97ae95. SHA256 of predictions.csv.gz: 11dc413033af9ddfda6e16b2b9d1a2a067ad6482e186453282d6c1f38625937c. Source prices are Energinet DayAheadPrices, EUR/MWh, under CC BY 4.0. Source archive hash: 93ccd57867b2eae79705659e84a4aa8f1913b3a714204ccb859316a964ef7da2. No new source download or model training is needed to reproduce this dispatch replay.

Run both DK1 and DK2 for every local delivery day from 1 July through 30 September 2026 (92 days per area). Decisions are made at 10:00 Europe/Copenhagen on D−1. Use Nordcast's original validation-locked choices: ridge for DK1, boosted quantile median for DK2. Weekly seasonal is the comparison. Nordcast's delayed historical-price features and monthly refit protocol are inherited; see its linked protocol. The archive can contain price revisions and is not historical-vintage data.

## Hypothetical asset and optimization

- 1 MW grid charging/discharging power; 2 MWh usable cell capacity.
- Cell state starts and ends each local day at exactly 1 MWh (50%). This imposes no free overnight reset because consecutive boundary states agree. No cross-day optimization.
- Charge and discharge efficiencies each 0.95; round-trip efficiency 0.9025.
- Grid throughput fee: EUR 2 per MWh imported or exported.
- Wear proxy: EUR 8 per MWh removed from the cell (grid export divided by 0.95).
- Prices, fees and wear are fixed; these costs are illustrative, not quoted tariffs or a validated degradation model.
- Native 15-minute intervals, including 92/100-quarter daylight-saving days when applicable.
- State equation: next SOC = SOC + 0.95 × charge MW × 0.25 − discharge MW × 0.25 / 0.95.
- Mixed-integer linear optimization maximizes forecast net cash flow. A binary mode prevents simultaneous charging and discharging, including at negative prices. No smoothing, ramp limits, self-discharge, reserve markets or cycle cap.
- SciPy/HiGHS: relative gap 1e−6; 20-second limit per solve. Accept only status 0 and independently validated physical/accounting constraints; otherwise stop the benchmark and report the failure, with no silently substituted schedule.

Policies: frozen selected-model dispatch, weekly-lag dispatch, idle, and perfect-price hindsight dispatch. Each uses identical asset constraints and costs. Idle is always feasible. Report solver gap and net objective upper bound; perfect-price realized cash flow is an approximate attainable hindsight comparator, within the recorded solver gap of the upper bound.

Forecast policies commit before the modeled clearing-price knowledge time and settle unchanged at actual cleared prices with full fills. This is an early-commitment scheduling experiment. Scheduling after day-ahead prices are published is a different information set and does not need these forecasts. No actual exchange, limit orders, imbalance settlement or battery hardware. Forecasts are not allowed to inspect actual target-day prices; hindsight is explicitly separate.

## Accounting and reporting

Publish full-precision interval charge/discharge/SOC, gross energy cash flow, fee, wear and net cash flow, plus daily solver records. Sum costs from actual prices, never forecast prices. Equivalent full cycles = cell energy discharged / 2 MWh. Since daily initial and final SOC agree, total grid import minus export equals losses. Summaries: 92-day net/gross revenue, costs, throughput, losses, cycles, profitable/losing days, worst day, comparison with weekly, idle and hindsight. Display all policies even if the selected forecast loses.

No return-on-investment, payback or real-market profitability claim: omit capital cost, financing, grid tariffs, taxes, capacity payments and market frictions. No confidence interval implying an independent, previously unseen sample. UI may linearly scale the entire asset (power and capacity together), retaining its duration and schedules, and must label that assumption.
