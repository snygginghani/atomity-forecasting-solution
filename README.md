# Cloud workload forecasting: short history, explicit limits

[![Verify solution](https://github.com/snygginghani/atomity-forecasting-solution/actions/workflows/verify.yml/badge.svg)](https://github.com/snygginghani/atomity-forecasting-solution/actions/workflows/verify.yml)

Solution to the [Atomity forecasting challenge](https://github.com/atomityhq/forecasting-challenge), using the exact data-v1 Azure release. Original assignment, contracts, sources and license are retained.

**Result:** ridge autoregression reduced CPU holdout MAE from **0.1468 to 0.0987 percentage points (32.7%)**. VM-count persistence was exact because this release selects complete VM traces. This cannot establish churn forecasting ability.

Read the [six-page report](reports/final_report.pdf) or its [Markdown source](reports/final_report.md). AI assistance was used in implementation, analysis and drafting; the candidate should review and understand the work before submission.

## Install and reproduce

Python 3.11+; tested with Python 3.13.3, NumPy 2.4.6, pandas 3.0.2, matplotlib 3.10.9, pytest 9.1.1. A fresh virtual environment with NumPy 2.5.4 and pandas 3.1.0 also passed all tests and reproduced the prediction CSV byte-for-byte. No GPU or external service is needed. Model fitting is deterministic and uses NumPy only. Allow about 1 GB free memory and 120 MB for the download.

```bash
python -m venv .venv
```

Activate on Windows PowerShell with `.venv\Scripts\Activate.ps1`; on Linux/macOS use `source .venv/bin/activate`.

```bash
python -m pip install -e ".[dev,analysis]"
python -m cwfc.download --data challenge_data
python -m pytest -q
python -m cwfc.predict --data challenge_data --output predictions.csv
```

The last command is the single prediction command. It validates the source, constructs targets, selects models exclusively inside the training window and writes exactly 24 rows in the required column order. It writes `reports/artifacts/selection.json` with training/prediction hashes, model choices, validation scores and environment versions. It runs in a few seconds after installation, without manual CSV edits.

The downloader fetches the fixed 116,513,018-byte release, safely extracts four named files and verifies the SHA-256 manifest. Alternatively download [data-v1.tar.gz](https://github.com/atomityhq/forecasting-challenge/releases/tag/data-v1) and put `vm_cpu_readings.csv.gz`, `vm_metadata.csv.gz`, `DATA_CARD.md` and `SHA256SUMS` directly inside `challenge_data/`.

After predictions are frozen:

```bash
python -m cwfc.evaluate --data challenge_data --predictions predictions.csv
python -m cwfc.analyze --data challenge_data
```

Evaluation checks prediction and training hashes before scoring. Analysis requires evaluation artifacts; neither command changes model choices. On replacement data use generated metrics and tables: the narrative report is specific to the supplied release. Optional PDF rebuild: `pip install reportlab`, then `python scripts/build_report.py`.

## Decisions and information availability

- Targets: distinct observed VM count and unweighted mean avg_cpu, at the original 300-second cadence. Source-relative seconds are preserved; no invented date or timezone.
- Quality: reject missing/nonfinite/out-of-range CPU, duplicate VM/timestamp pairs, inconsistent CPU ordering, metadata mismatch and global grid gaps. No imputation. Partial population coverage is counted as observed, per contract.
- Split: first 110 timestamps train, final 24 test. Origins 38, 62 and 86 each forecast 24 steps without updating from validation actuals.
- Candidates: persistence, 6/12/24-point mean, all-history mean, damped local trend, ridge AR(6). Lowest pooled validation MAE wins independently per target; baseline-first tie breaking. Lag count, penalty 10 and damping 0.8 are fixed rather than tuned on holdout.
- Recursive forecasts use training lags and then their own predictions. Scaling is fitted at each origin. Metadata categories are descriptive only; lifetimes, deletion times and source CPU summaries never become predictors.
- The 90th percentile of selected-model validation absolute errors is an empirical envelope, **not a calibrated 90% prediction interval**. Only three blocks are available and their errors also select the model.

For custom smoke data, the final `--horizon` timestamps are test, default 24. Smaller examples can use `--horizon 4`. At least eight initial training points plus a full validation block are required. Origins adapt to history length. Counts, forecasts and timestamps derive from input, without hard-coded VM IDs or target values. A manifest may be absent for custom datasets.

## Files and evidence

| File | Purpose |
|---|---|
| src/cwfc/data.py | Checksums, strict validation, target construction |
| src/cwfc/models.py | Candidate forecasts and temporal selection |
| src/cwfc/predict.py | Training-only selection and required output |
| src/cwfc/evaluate.py | Separate evaluation of frozen predictions |
| src/cwfc/analyze.py | Reproducible EDA, segments, charts and diagnostics |
| reports/artifacts/ | Small audit tables, JSON metrics and plots |
| tests/test_pipeline.py | Holdout perturbation, tiny dataset and integrity tests |

Predictions and small report artifacts are included. Release data, environments and caches are excluded from Git and the submission archive. Source code plus generated analysis is the notebook-equivalent deliverable.

GitHub Actions runs the tests on Python 3.11 and 3.13. The Python 3.13 job also downloads the verified release, regenerates predictions, runs evaluation and analysis, and checks that the forecasts match the submitted values. See [PROVENANCE.md](PROVENANCE.md) for the upstream starter attribution.

## Operational conclusion

Use forecasts as an advisory aggregate-demand signal with an error margin, segment monitoring and reactive safeguards. A low average can hide hot VMs. Unequal core sizes and censored metadata prevent interpreting this unweighted average as physical core demand or deriving server counts.
