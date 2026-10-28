# Dataset Contract

## 1. Upstream source

Microsoft Azure Public Dataset V2:

https://github.com/Azure/AzurePublicDataset

Official V2 documentation:

https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md

The full upstream V2 dataset contains a much larger 30-day VM trace. This challenge distributes a small, deterministic subset suitable for a take-home exercise.

## 2. Challenge release

The candidate dataset is the fixed **`data-v1`** release of this repository.

The release is a real, curated subset of Azure Public Dataset V2.

Extract the release so that the repository looks like:

```text
challenge_data/
├── vm_cpu_readings.csv.gz
├── vm_metadata.csv.gz
├── DATA_CARD.md
└── SHA256SUMS
```

The CPU dataset contains exactly 10,000 VMs × 134 observations = 1,340,000 observations. Each VM has observations at five-minute intervals, spanning approximately 11.1 hours.

## 3. Row-level fields

### `vm_cpu_readings.csv.gz`

Columns:

| Field | Meaning |
|---|---|
| `timestamp` | observation timestamp in seconds relative to the source trace |
| `vm_id` | anonymized VM identifier |
| `min_cpu` | minimum CPU utilization during the five-minute interval |
| `max_cpu` | maximum CPU utilization during the five-minute interval |
| `avg_cpu` | average CPU utilization during the five-minute interval |

### `vm_metadata.csv.gz`

Columns:

| Field | Meaning |
|---|---|
| `vm_id` | anonymized VM identifier |
| `subscription_id` | anonymized subscription identifier |
| `deployment_id` | anonymized deployment identifier |
| `timestamp_vm_created` | VM creation timestamp |
| `timestamp_vm_deleted` | VM deletion timestamp |
| `max_cpu` | source VM-level maximum CPU statistic |
| `avg_cpu` | source VM-level average CPU statistic |
| `p95_max_cpu` | source VM-level P95 maximum CPU statistic |
| `vm_category` | source VM workload category |
| `virtual_core_bucket` | bucketed virtual-core count |
| `memory_gb_bucket` | bucketed VM memory |

## 4. Required derived targets

Construct these aggregate time series from the VM-level readings.

### `active_vm_count`

For timestamp `t`:

```text
active_vm_count(t) =
    number of distinct VM IDs with a valid CPU observation at t
```

A VM must be counted at most once within a timestamp.

### `aggregate_cpu_utilization`

For timestamp `t`:

```text
aggregate_cpu_utilization(t) =
    mean of VM-level avg_cpu values at t
```

Express the result as a percentage in `[0,100]`.

These two targets are required. Candidates may introduce additional targets as extensions.

## 5. Time handling

Treat the source timestamps as a five-minute observation grid.

Candidates should:

- detect gaps and duplicates;
- preserve the chronological ordering;
- document any resampling;
- avoid inventing target values for missing source observations without justification.

The challenge dataset has 134 observations per VM. The required forecasting split is described in `ASSIGNMENT.md`.

## 6. Forecast holdout

For the core challenge, construct the aggregate target series and use:

- the first 110 observations as the public training window;
- the final 24 observations as the two-hour holdout horizon.

The final 24 observations are part of the public release, so candidates must follow the stated holdout protocol and must not use those target values during model fitting, feature selection, hyperparameter tuning, or model selection.

Do not reconstruct omitted upstream records or claim access to private evaluation material.
