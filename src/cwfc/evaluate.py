"""Post-selection evaluation. Never invokes model selection."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .data import TARGETS, load_data, sha256
from .predict import frame_hash
from .models import bounded_forecast
from .metrics import mae, rmse, smape


def metrics(actual, pred, baseline, peak_threshold):
    actual, pred, baseline = map(lambda v: np.asarray(v, float), (actual, pred, baseline))
    peak = actual >= peak_threshold
    base_error = mae(actual, baseline)
    return dict(mae=mae(actual, pred), rmse=rmse(actual, pred), smape=smape(actual, pred),
                baseline_mae=base_error,
                relative_mae=mae(actual, pred) / base_error if base_error > 0 else None,
                peak_threshold=float(peak_threshold), peak_n=int(peak.sum()),
                peak_mae=mae(actual[peak], pred[peak]) if peak.any() else None,
                worst_underprediction=float(np.maximum(actual - pred, 0).max()),
                bias=float(np.mean(pred - actual)))


def run(data, predictions, artifacts):
    artifacts = Path(artifacts)
    selection = json.loads((artifacts / 'selection.json').read_text())
    _, _, series = load_data(data)
    n = selection['n_train']
    train, test = series.iloc[:n], series.iloc[n:]
    if frame_hash(train) != selection['train_sha256']:
        raise ValueError('Training observations differ from frozen run')
    if sha256(predictions) != selection['predictions_sha256']:
        raise ValueError('Predictions changed after selection')
    pred = pd.read_csv(predictions)
    if list(pred.columns) != ['timestamp'] + TARGETS or len(pred) != selection['horizon']:
        raise ValueError('Invalid prediction schema/length')
    if not np.array_equal(pred.timestamp, test.timestamp) or pred.timestamp.duplicated().any():
        raise ValueError('Prediction timestamp mismatch')
    if not np.isfinite(pred.to_numpy(float)).all() or (pred.active_vm_count < 0).any() or not pred.aggregate_cpu_utilization.between(0, 100).all():
        raise ValueError('Invalid prediction values')
    envelopes = pd.read_csv(artifacts / 'forecast_envelopes.csv')
    scores, detail = {}, test.reset_index(drop=True).copy()
    for target in TARGETS:
        baseline = bounded_forecast(train[target], len(test), 'persistence', target)
        threshold = train[target].quantile(.9)
        scores[target] = metrics(test[target], pred[target], baseline, threshold)
        scores[target]['envelope_coverage'] = float(np.mean(
            (test[target].to_numpy() >= envelopes[target + '_lower']) &
            (test[target].to_numpy() <= envelopes[target + '_upper'])))
        scores[target]['baseline'] = metrics(test[target], baseline, baseline, threshold)
        detail[target + '_prediction'] = pred[target]
        detail[target + '_baseline'] = baseline
    detail.to_csv(artifacts / 'holdout_errors.csv', index=False)
    (artifacts / 'holdout_metrics.json').write_text(json.dumps(scores, indent=2) + '\n')
    print(json.dumps(scores, indent=2))
    return scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='challenge_data')
    parser.add_argument('--predictions', default='predictions.csv')
    parser.add_argument('--artifacts', default='reports/artifacts')
    args = parser.parse_args()
    run(args.data, args.predictions, args.artifacts)
