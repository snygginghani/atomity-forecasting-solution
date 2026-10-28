# Challenge Dataset Release

The hiring dataset is distributed as a GitHub Release asset so that the fixed candidate data can be versioned separately from the source repository.

## Required release

Use the fixed release:

```text
data-v1
```

The release asset is:

```text
data-v1.tar.gz
```

Download it from:

https://github.com/atomityhq/forecasting-challenge/releases/tag/data-v1

After extraction:

```text
challenge_data/
├── vm_cpu_readings.csv.gz
├── vm_metadata.csv.gz
├── DATA_CARD.md
└── SHA256SUMS
```

The release contains:

- 10,000 selected VMs;
- 134 CPU observations per VM;
- 1,340,000 CPU observation rows;
- five-minute sampling;
- approximately 11.1 hours of observations per VM.

## Integrity

Verify the included checksums before starting work:

```bash
cd challenge_data
sha256sum -c SHA256SUMS
```

Expected:

```text
vm_cpu_readings.csv.gz: OK
vm_metadata.csv.gz: OK
DATA_CARD.md: OK
```

## Source attribution

The dataset is a curated subset of Microsoft's Azure Public Dataset V2. See `SOURCES.md` and the bundled `DATA_CARD.md` for source attribution and dataset information.
