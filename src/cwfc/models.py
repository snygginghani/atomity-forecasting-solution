"""Small, predeclared candidate set for a short nonseasonal history."""
import numpy as np

CANDIDATES = ('persistence', 'mean_6', 'mean_12', 'mean_24', 'historical_mean',
              'damped_trend_12', 'ridge_ar_6')


def forecast(values, horizon, model):
    y = np.asarray(values, dtype=float)
    if y.ndim != 1 or len(y) == 0 or not np.isfinite(y).all() or horizon < 1:
        raise ValueError('Expected finite nonempty history and positive horizon')
    if model == 'persistence':
        return np.repeat(y[-1], horizon)
    if model.startswith('mean_'):
        return np.repeat(y[-int(model.split('_')[1]):].mean(), horizon)
    if model == 'historical_mean':
        return np.repeat(y.mean(), horizon)
    if model == 'damped_trend_12':
        recent = y[-12:]
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0] if len(recent) > 1 else 0.
        # Anchor on current observation; trend contribution saturates with horizon.
        return y[-1] + slope * np.cumsum(0.8 ** np.arange(1, horizon + 1))
    if model == 'ridge_ar_6':
        p = min(6, max(1, len(y) // 4))
        center = y.mean()
        scale = max(float(y.std()), 1e-8)
        z = (y - center) / scale
        X = np.array([z[t-p:t][::-1] for t in range(p, len(z))])
        response = z[p:]
        # Standardize within each origin; fit intercept without penalizing it.
        xm, ym = X.mean(axis=0), response.mean()
        Xc = X - xm
        beta = np.linalg.solve(Xc.T @ Xc + 10 * np.eye(p), Xc.T @ (response - ym))
        history, out = list(z), []
        for _ in range(horizon):
            pred = float(ym + (np.array(history[-p:][::-1]) - xm) @ beta)
            history.append(pred)
            out.append(center + scale * pred)
        return np.array(out)
    raise ValueError(f'Unknown model: {model}')


def bounded_forecast(values, horizon, model, target):
    return np.clip(forecast(values, horizon, model), 0,
                   100 if target == 'aggregate_cpu_utilization' else np.inf)


def origins(n, horizon):
    """Three disjoint full-horizon blocks when history permits; end at n."""
    first = n - 3 * horizon
    if first >= 8:
        return list(range(first, n - horizon + 1, horizon))
    return list(range(max(8, n - 2 * horizon), n - horizon + 1, horizon))


def select_model(values, horizon, target):
    y = np.asarray(values, float)
    splits = origins(len(y), horizon)
    if not splits:
        raise ValueError('Insufficient training data for a full-horizon validation; reduce --horizon')
    records = []
    for model in CANDIDATES:
        for origin in splits:
            pred = bounded_forecast(y[:origin], horizon, model, target)
            for h, (actual, estimate) in enumerate(zip(y[origin:origin+horizon], pred), 1):
                records.append(dict(target=target, model=model, origin=origin, horizon=h,
                                    actual=float(actual), prediction=float(estimate)))
    # Stable candidate order breaks numerical ties toward the simpler baseline.
    scores = {m: float(np.mean([abs(r['actual'] - r['prediction']) for r in records if r['model'] == m]))
              for m in CANDIDATES}
    best = min(scores.values())
    chosen = next(m for m in CANDIDATES if scores[m] <= best + 1e-10)
    errors = [abs(r['actual'] - r['prediction']) for r in records if r['model'] == chosen]
    # Descriptive error envelope, not calibrated coverage after model selection.
    radius = float(np.quantile(errors, 0.9, method='higher'))
    return chosen, radius, records, scores
