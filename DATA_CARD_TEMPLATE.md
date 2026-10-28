# Challenge Dataset v1 — Data Card

## Source

Microsoft Azure Public Dataset V2:

https://github.com/Azure/AzurePublicDataset

Official V2 documentation:

https://github.com/Azure/AzurePublicDataset/blob/master/AzurePublicDatasetV2.md

## Derivative

This release is a curated subset of the upstream Azure V2 VM workload trace for the Cloud Workload Forecasting Challenge.

## Curation

- Upstream dataset: Microsoft Azure Public Dataset V2
- Source CPU shards: first three chronological CPU-reading shards
- Sampling method: deterministic stratified selection
- VM selection rule: select complete 134-observation VM traces, stratified by VM category and virtual-core bucket; rank VM IDs using a stable SHA-256 ordering within each stratum
- Number of VMs retained: 10,000
- CPU observations retained: 1,340,000
- Observation cadence: five minutes
- Per-VM observation span: approximately 11.1 hours
- Included files: `vm_cpu_readings.csv.gz`, `vm_metadata.csv.gz`, `DATA_CARD.md`, `SHA256SUMS`

The resulting VM selection is fixed for `data-v1`. No private sampling seed is required.

## Semantics

The release preserves the source dataset's anonymized VM workload semantics. See the upstream V2 documentation and the bundled `DATA_CARD.md` for authoritative source information.

## Integrity

The release includes a `SHA256SUMS` file covering all three content files.

Verify with:

```bash
sha256sum -c SHA256SUMS
```

## Attribution

Please retain attribution to the Microsoft Azure Public Dataset and follow the upstream dataset's current license and usage terms.
