"""Strict observation-based targets. No filling or metadata-based activity inference."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd

TARGETS = ['active_vm_count', 'aggregate_cpu_utilization']


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_release(directory):
    directory = Path(directory)
    manifest = directory / 'SHA256SUMS'
    if not manifest.exists():
        return {'manifest': 'absent (permitted for smoke datasets)'}
    results = {}
    for line in manifest.read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.lstrip('*')
        path = (directory / name).resolve()
        if not path.is_relative_to(directory.resolve()):
            raise ValueError('Unsafe checksum path')
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f'Checksum mismatch: {name}')
        results[name] = actual
    return results


def load_data(directory):
    directory = Path(directory)
    readings = pd.read_csv(directory / 'vm_cpu_readings.csv.gz')
    metadata = pd.read_csv(directory / 'vm_metadata.csv.gz')
    required = ['timestamp', 'vm_id', 'min_cpu', 'max_cpu', 'avg_cpu']
    if not set(required).issubset(readings.columns):
        raise ValueError('Missing CPU columns')
    if readings[required].isna().any().any():
        raise ValueError('Missing readings: refusing to impute or silently change the population')
    numeric = readings[['timestamp', 'min_cpu', 'max_cpu', 'avg_cpu']].to_numpy(float)
    if not np.isfinite(numeric).all():
        raise ValueError('Non-finite readings')
    if (readings.timestamp % 1 != 0).any():
        raise ValueError('Timestamps must be integer source-relative seconds')
    if not readings[['min_cpu', 'max_cpu', 'avg_cpu']].apply(lambda s: s.between(0, 100).all()).all():
        raise ValueError('CPU must be in [0,100]')
    if ((readings.min_cpu > readings.avg_cpu) | (readings.avg_cpu > readings.max_cpu)).any():
        raise ValueError('Expected min_cpu <= avg_cpu <= max_cpu')
    # Reject even identical duplicates: a repaired dataset needs a documented provenance.
    if readings.duplicated(['timestamp', 'vm_id']).any():
        raise ValueError('Duplicate VM/timestamp observations')
    if metadata.vm_id.isna().any() or metadata.vm_id.duplicated().any():
        raise ValueError('Metadata must contain one row per VM')
    if set(metadata.vm_id) != set(readings.vm_id):
        raise ValueError('Metadata/CPU population mismatch')
    targets = readings.groupby('timestamp', sort=True).agg(
        active_vm_count=('vm_id', 'nunique'), aggregate_cpu_utilization=('avg_cpu', 'mean')
    ).reset_index()
    targets['timestamp'] = targets.timestamp.astype('int64')
    if len(targets) < 2 or not np.all(np.diff(targets.timestamp) == 300):
        raise ValueError('Expected a complete 300-second timestamp grid; no gap filling is assumed')
    return readings, metadata, targets
