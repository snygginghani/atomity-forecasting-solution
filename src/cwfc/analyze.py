"""Reproducible descriptive analysis; model choices live only in predict.py."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import load_data, TARGETS
from .evaluate import metrics


def run(data, artifacts):
    artifacts = Path(artifacts)
    selection = json.loads((artifacts / 'selection.json').read_text())
    readings, meta, series = load_data(data)
    n = selection['n_train']
    train = series.iloc[:n]
    cpu = readings[readings.timestamp <= train.timestamp.iloc[-1]].copy()
    counts = readings.groupby('vm_id').size()
    cadence = readings.sort_values(['vm_id', 'timestamp']).groupby('vm_id').timestamp.diff().dropna()
    first, last = int(series.timestamp.min()), int(series.timestamp.max())
    summary = dict(rows=len(readings), vms=int(readings.vm_id.nunique()), timestamps=len(series),
                   first_timestamp=first, last_timestamp=last, elapsed_hours=(last-first)/3600,
                   observation_counts=counts.value_counts().to_dict(),
                   cadence_counts=cadence.value_counts().to_dict(),
                   missing_values=readings.isna().sum().to_dict(),
                   duplicates=int(readings.duplicated(['vm_id', 'timestamp']).sum()),
                   observed_arrivals=int((readings.groupby('vm_id').timestamp.min() > first).sum()),
                   observed_departures=int((readings.groupby('vm_id').timestamp.max() < last).sum()),
                   train_cpu_quantiles=cpu.avg_cpu.quantile([0,.25,.5,.75,.9,.95,.99,1]).to_dict(),
                   train_zero_cpu_fraction=float((cpu.avg_cpu == 0).mean()),
                   train_above80_fraction=float((cpu.avg_cpu >= 80).mean()),
                   train_mean_cpu=float(cpu.avg_cpu.mean()),
                   train_aggregate_min=float(train.aggregate_cpu_utilization.min()),
                   train_aggregate_max=float(train.aggregate_cpu_utilization.max()),
                   train_min_timestamp=int(train.loc[train.aggregate_cpu_utilization.idxmin(), 'timestamp']),
                   train_max_timestamp=int(train.loc[train.aggregate_cpu_utilization.idxmax(), 'timestamp']),
                   train_acf={str(lag):float(train.aggregate_cpu_utilization.autocorr(lag)) for lag in [1,6,12,24]},
                   metadata_preexisting=int((meta.timestamp_vm_created <= first).sum()),
                   metadata_deleted_in_window=int(meta.timestamp_vm_deleted.between(first, last).sum()),
                   metadata_lifetime_hours=(((meta.timestamp_vm_deleted - meta.timestamp_vm_created)/3600)
                                            .quantile([0,.5,.9,1]).to_dict()))
    joined = cpu.merge(meta[['vm_id','vm_category','virtual_core_bucket','memory_gb_bucket']],
                       on='vm_id', validate='many_to_one')
    segment_rows = []
    for field in ['vm_category','virtual_core_bucket','memory_gb_bucket']:
        for label, group in joined.groupby(field, observed=True):
            time = group.groupby('timestamp').avg_cpu.mean()
            segment_rows.append(dict(dimension=field, segment=str(label), vms=group.vm_id.nunique(),
                                     mean_cpu=group.avg_cpu.mean(), median_cpu=group.avg_cpu.median(),
                                     p95_cpu=group.avg_cpu.quantile(.95),
                                     above80_fraction=(group.avg_cpu >= 80).mean(),
                                     aggregate_std=time.std(), contribution_pp=group.avg_cpu.sum()/len(cpu)))
    pd.DataFrame(segment_rows).to_csv(artifacts / 'segments.csv', index=False)
    (artifacts / 'data_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    series.to_csv(artifacts / 'targets.csv', index=False)
    validation = pd.read_csv(artifacts / 'validation_predictions.csv')
    fold_rows = []
    for (target, model, origin), frame in validation.groupby(['target','model','origin']):
        base = validation[(validation.target == target) & (validation.model == 'persistence') &
                          (validation.origin == origin)].sort_values('horizon')
        frame = frame.sort_values('horizon')
        threshold = train[target].iloc[:origin].quantile(.9)
        fold_rows.append(dict(target=target, model=model, origin=int(origin),
                              **metrics(frame.actual, frame.prediction, base.prediction, threshold)))
    pd.DataFrame(fold_rows).to_csv(artifacts / 'validation_metrics.csv', index=False)
    holdout = pd.read_csv(artifacts / 'holdout_errors.csv')
    bands = pd.read_csv(artifacts / 'forecast_envelopes.csv')
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False})
    hours = (series.timestamp - first)/3600
    fig, axes = plt.subplots(2,1, figsize=(10,4.4), sharex=True, layout='constrained',
                             gridspec_kw={'height_ratios':[1,3]})
    for ax, target in zip(axes, TARGETS):
        ax.plot(hours, series[target], label='Observed', color='#16324f')
        hx = hours.iloc[n:].to_numpy()
        ax.plot(hx, holdout[target+'_prediction'], label='Selected forecast', color='#db5c30')
        ax.plot(hx, holdout[target+'_baseline'], label='Persistence', color='#777777', linestyle='--')
        ax.fill_between(hx, bands[target+'_lower'], bands[target+'_upper'], color='#db5c30', alpha=.15,
                        label='Training-validation error envelope')
        ax.axvline((hours.iloc[n-1]+hours.iloc[n])/2, color='black', linestyle=':')
        ax.set_ylabel('Observed VMs' if target == TARGETS[0] else 'Mean CPU (%)')
        if target == TARGETS[0]:
            ax.set_ylim(series[target].min() - 5, series[target].max() + 5)
            ax.ticklabel_format(axis='y', style='plain', useOffset=False)
            ax.set_yticks([series[target].min(), series[target].max()+5])
    axes[1].legend(fontsize=8, loc='upper left', ncol=2)
    axes[1].set_xlabel('Hours since first source timestamp (no calendar/timezone assumed)')
    fig.savefig(artifacts / 'forecast.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1,2, figsize=(10,3.6), layout='constrained')
    axes[0].hist(cpu.avg_cpu, bins=np.linspace(0,100,51), color='#16324f')
    axes[0].set_yscale('log')
    axes[0].set_xlabel('VM five-minute mean CPU (%)')
    axes[0].set_ylabel('Training observations (log scale)')
    for label, group in joined.groupby('vm_category'):
        time = group.groupby('timestamp').avg_cpu.mean()
        axes[1].plot((time.index-first)/3600,time,label=label)
    axes[1].set_xlabel('Hours since first source timestamp')
    axes[1].set_ylabel('Segment mean CPU (%)')
    axes[1].legend(fontsize=8)
    fig.savefig(artifacts / 'workload.png', dpi=160)
    plt.close(fig)
    err_rows = []
    for target in TARGETS:
        chosen = validation[(validation.target == target) & (validation.model == selection['models'][target])].copy()
        chosen['absolute_error'] = abs(chosen.actual - chosen.prediction)
        chosen['horizon_block'] = ((chosen.horizon-1)//6)*30
        for minutes, group in chosen.groupby('horizon_block'):
            err_rows.append(dict(target=target, minutes_start=int(minutes+5), minutes_end=int(minutes+30),
                                 mae=float(group.absolute_error.mean())))
    pd.DataFrame(err_rows).to_csv(artifacts / 'horizon_metrics.csv', index=False)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', default='challenge_data')
    parser.add_argument('--artifacts', default='reports/artifacts')
    args = parser.parse_args()
    run(args.data, args.artifacts)
