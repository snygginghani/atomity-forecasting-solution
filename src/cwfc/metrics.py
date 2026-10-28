from __future__ import annotations

import numpy as np


def mae(y_true, y_pred) -> float:
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    if a.shape != b.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    return float(np.mean(np.abs(a - b)))


def rmse(y_true, y_pred) -> float:
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    if a.shape != b.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    return float(np.sqrt(np.mean((a - b) ** 2)))


def smape(y_true, y_pred, eps: float = 1e-8) -> float:
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    if a.shape != b.shape:
        raise ValueError("y_true and y_pred must have the same shape")
    denom = np.maximum(np.abs(a) + np.abs(b), eps)
    return float(np.mean(2.0 * np.abs(a - b) / denom) * 100.0)


def normalized_mae(y_true, y_pred, baseline_pred) -> float:
    model_mae = mae(y_true, y_pred)
    baseline_mae = mae(y_true, baseline_pred)
    if baseline_mae == 0:
        return 0.0 if model_mae == 0 else float("inf")
    return float(model_mae / baseline_mae)
