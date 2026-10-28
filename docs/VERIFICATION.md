# Publication verification — 28 October 2026

Code and data release: `7b5f8a5f848410ee8858d16c92c15ddd19c8c929`.

- All 28 published file paths and Git blob hashes match the staged local project.
- Local verification: 20 Python tests and 6 JavaScript tests passed.
- [GitHub Tests run 40713724211](https://github.com/Ehsan-Ch/danish-battery-dispatch-lab/actions/runs/40713724211): success. Python 3.11, Python 3.12 and Node 22 jobs all passed, including installation and tests.
- [GitHub Pages run 40713795886](https://github.com/Ehsan-Ch/danish-battery-dispatch-lab/actions/runs/40713795886): success for the same release.
- [Public preview](https://ehsan-ch.github.io/danish-battery-dispatch-lab/) loaded the complete report and charts. Changed area, policy, day and asset size successfully.
- Downloaded the public DK2 weekly-policy replay for 30 September at 0.5 MW / 1 MWh. It contained 96 intervals. Summed net cash flow €175.1463949506 matched the full-precision expected €175.1463942767 within display-export rounding tolerance (€0.002).
- Local browser testing also checked hindsight, idle and doubled asset scaling.

The documentation-only verification commit does not change code or numerical results. Recorded checks apply to the release above.
