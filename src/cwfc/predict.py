"""Generate forecasts using training observations only; no holdout scoring here."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from .data import TARGETS, load_data, verify_release, sha256
from .models import select_model, bounded_forecast, origins


def frame_hash(frame):
    return hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()


def run(data, output, artifacts, horizon=24):
    checksums = verify_release(data)
    _, _, series = load_data(data)
    train = series.iloc[:-horizon].copy()
    future = series.iloc[-horizon:][['timestamp']].copy().reset_index(drop=True)
    if horizon < 1 or len(train) < 8:
        raise ValueError('Need positive horizon and at least eight training timestamps')
    artifacts = Path(artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)
    decisions = dict(protocol='train-only selection; evaluate separately after freezing predictions',
                     horizon=horizon, n_train=len(train), origins=origins(len(train), horizon),
                     train_sha256=frame_hash(train), checksums=checksums,
                     environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__),
                     models={}, validation_mae={}, envelope_radius={})
    records, bounds = [], future.copy()
    for target in TARGETS:
        model, radius, rows, scores = select_model(train[target], horizon, target)
        future[target] = bounded_forecast(train[target], horizon, model, target)
        decisions['models'][target] = model
        decisions['validation_mae'][target] = scores
        decisions['envelope_radius'][target] = radius
        bounds[target + '_lower'] = np.maximum(0, future[target] - radius)
        bounds[target + '_upper'] = np.minimum(100 if target == TARGETS[1] else np.inf,
                                              future[target] + radius)
        records.extend(rows)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    future.to_csv(output, index=False, float_format='%.12g')
    decisions['predictions_sha256'] = sha256(output)
    pd.DataFrame(records).to_csv(artifacts / 'validation_predictions.csv', index=False)
    bounds.to_csv(artifacts / 'forecast_envelopes.csv', index=False)
    (artifacts / 'selection.json').write_text(json.dumps(decisions, indent=2) + '\n')
    print(json.dumps(decisions['models'], indent=2))
    return decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='challenge_data')
    parser.add_argument('--output', default='predictions.csv')
    parser.add_argument('--artifacts', default='reports/artifacts')
    parser.add_argument('--horizon', type=int, default=24)
    args = parser.parse_args()
    run(args.data, args.output, args.artifacts, args.horizon)


if __name__ == '__main__':
    main()
