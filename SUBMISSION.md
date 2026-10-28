# Submission Contract

## Required output

Your solution must produce:

```text
predictions.csv
```

with exactly these columns:

```text
timestamp,active_vm_count,aggregate_cpu_utilization
```

## Prediction requirements

- exactly 24 rows;
- one row for each timestamp in the final two-hour holdout;
- timestamps must match the holdout timestamps exactly, in chronological order;
- no duplicate timestamps;
- no missing predictions;
- all values must be finite numeric values;
- `active_vm_count >= 0`;
- `aggregate_cpu_utilization` should be in `[0,100]`.

Do not include an index column.

The final 24 target observations are the public holdout. Do not use their observed target values for fitting, feature selection, hyperparameter tuning, or model selection.

## Reproduction

Your README should expose one clear command that produces the prediction file from the supplied release data.

For example:

```bash
python -m your_package.predict   --data challenge_data   --output predictions.csv
```

The exact command is up to you.

A reviewer should be able to reproduce the submission from a clean checkout without manually editing the generated prediction file.

## Repository hygiene

Do not commit:

- credentials or secrets;
- virtual environments;
- generated caches;
- notebook checkpoints;
- large derived datasets;
- copies of the upstream Azure release.

## What reviewers will run

Reviewers may run your documented training/prediction command from a clean checkout and may replace the public challenge data with a tiny internal smoke dataset to verify that your pipeline is not hard-coded to the supplied files.
