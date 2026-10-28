import json
import numpy as np
import pandas as pd
import pytest
from cwfc.data import load_data
from cwfc.models import CANDIDATES, bounded_forecast, origins
from cwfc.predict import run
from cwfc.evaluate import run as evaluate


def tiny_data(path, corrupt_holdout=False):
    path.mkdir(exist_ok=True)
    rows = []
    for t in range(40):
        for vm in ['a','b']:
            cpu = (80 if corrupt_holdout and t >= 36 else 10 + np.sin(t/3))
            rows.append(dict(timestamp=300*(t+7), vm_id=vm, min_cpu=0, avg_cpu=cpu, max_cpu=100))
    pd.DataFrame(rows).to_csv(path/'vm_cpu_readings.csv.gz', index=False)
    pd.DataFrame({'vm_id':['a','b']}).to_csv(path/'vm_metadata.csv.gz', index=False)


def test_pipeline_is_invariant_to_holdout_labels(tmp_path):
    # End-to-end leakage test: replace all held-out readings; selection and CSV must not move.
    for name, change in [('original',False),('changed',True)]:
        data = tmp_path/name
        tiny_data(data, change)
        run(data, data/'pred.csv', data/'artifacts', horizon=4)
    a, b = tmp_path/'original', tmp_path/'changed'
    assert (a/'pred.csv').read_bytes() == (b/'pred.csv').read_bytes()
    sa = json.loads((a/'artifacts/selection.json').read_text())
    sb = json.loads((b/'artifacts/selection.json').read_text())
    assert sa == sb
    assert sa['n_train'] == 36
    assert sa['origins'] == [24,28,32]
    evaluate(a, a/'pred.csv', a/'artifacts')


def test_targets_and_duplicate_rejection(tmp_path):
    tiny_data(tmp_path)
    _, _, targets = load_data(tmp_path)
    assert (targets.active_vm_count == 2).all()
    assert targets.timestamp.iloc[0] == 2100
    path = tmp_path/'vm_cpu_readings.csv.gz'
    rows = pd.read_csv(path)
    pd.concat([rows, rows.iloc[:1]]).to_csv(path,index=False)
    with pytest.raises(ValueError, match='Duplicate'):
        load_data(tmp_path)


def test_rejects_grid_gaps_and_missing_readings(tmp_path):
    tiny_data(tmp_path)
    path = tmp_path/'vm_cpu_readings.csv.gz'
    rows = pd.read_csv(path)
    rows[rows.timestamp != 2400].to_csv(path,index=False)
    with pytest.raises(ValueError, match='grid'):
        load_data(tmp_path)
    rows.loc[0,'avg_cpu'] = np.nan
    rows.to_csv(path,index=False)
    with pytest.raises(ValueError, match='Missing'):
        load_data(tmp_path)


def test_models_constant_and_bounds():
    for model in CANDIDATES:
        pred = bounded_forecast(np.repeat(10000.,38),24,model,'active_vm_count')
        np.testing.assert_allclose(pred,10000,atol=1e-8)
        pred = bounded_forecast(np.arange(38)*3.,24,model,'aggregate_cpu_utilization')
        assert np.isfinite(pred).all() and (pred >= 0).all() and (pred <= 100).all()
    assert origins(110,24) == [38,62,86]
    for origin in origins(110,24):
        assert origin+24 <= 110


def test_evaluation_refuses_modified_predictions(tmp_path):
    tiny_data(tmp_path)
    run(tmp_path, tmp_path/'pred.csv', tmp_path/'artifacts',4)
    with (tmp_path/'pred.csv').open('a') as stream:
        stream.write('\n')
    with pytest.raises(ValueError, match='changed'):
        evaluate(tmp_path,tmp_path/'pred.csv',tmp_path/'artifacts')
