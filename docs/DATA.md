# Inputs, attribution and reproducibility

## Price source

Energinet, [DayAheadPrices](https://www.energidataservice.dk/tso-electricity/DayAheadPrices), EUR/MWh for DK1 and DK2. See [metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices), [API guide](https://www.energidataservice.dk/guides/api-guides) and [terms](https://www.energidataservice.dk/terms-and-conditions). Source data is available under Creative Commons Attribution 4.0. Source-derived data and numerical reports in this repository retain that attribution and license.

Nordcast retrieved the source archive on 24 October 2026 at 14:35:47 UTC. It contains 70,080 native-quarter rows covering 1 October 2025 inclusive through 1 October 2026 exclusive, Danish local dates. Its raw SHA256 is `93ccd57867b2eae79705659e84a4aa8f1913b3a714204ccb859316a964ef7da2`. Metadata SHA256 is `f96149b61c23e1c85ce2023b9859fb250d178cf83445f6e488bdde2a0410a162`.

## Forecast dependency

Cellar includes the unmodified compressed [Nordcast predictions archive](https://github.com/Ehsan-Ch/danish-power-forecast-lab/blob/a8244399f0886d07ddafbe1d71b757abcb97ae95/reports/benchmark/predictions.csv.gz), SHA256 `11dc413033af9ddfda6e16b2b9d1a2a067ad6482e186453282d6c1f38625937c`.

See the [upstream protocol](https://github.com/Ehsan-Ch/danish-power-forecast-lab/blob/a8244399f0886d07ddafbe1d71b757abcb97ae95/docs/PROTOCOL.md). Prices are deemed available only after delivery end plus 24 hours, a conservative research assumption rather than observed publication timing. Forecast features use 72/96/168/336-hour lags and calendar variables. Models refit monthly on eligible history. Original June validation locks ridge for DK1 and boosted median for DK2. Cellar adds no target-day weather or realized demand.

Only test-partition weekly and selected-model rows are read for the dispatch experiment. Hash verification is followed by checks for all 184 area-days, expected local-day UTC intervals, duplicated keys, finite values, correct issue time and agreement of actual prices between model rows. The included archive also contains unused validation and other-model predictions so its original hash is preserved.

## Derived files

The mixed-integer schedules and their accounting are new Cellar outputs. `reports/results.json` records the frozen Cellar protocol hash, software versions, source hash and per-day solver diagnostics. Compressed interval CSV uses reproducible gzip timestamp zero. Daily schedules in JSON are rounded to seven decimals for display; the compressed journal holds full-precision solver output. The UI's downloadable chosen-day CSV is explicitly a display-data export.

All days in this sample have 96 intervals. UTC-keyed day generation also handles 92/100 intervals and is tested against Danish DST changes. Loss per interval in the journal is net grid import, which can be negative during discharge; only its daily sum, under equal boundary SOC, is the physical energy loss.

## Solver reference

The optimization uses [SciPy's documented MILP interface](https://docs.scipy.org/doc/scipy-1.15.3/reference/generated/scipy.optimize.milp.html) backed by HiGHS. No code is copied from its documentation. SciPy and NumPy versions are pinned in requirements.txt; MIT applies to Cellar code, not third-party dependencies or Energinet data.
