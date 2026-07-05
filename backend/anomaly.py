import pandas as pd
import numpy as np


def detect_anomalies(df: pd.DataFrame, window=7, z_threshold=2.5):
    df = df.sort_values('date').copy()
    results = []

    for (loc, sym), group in df.groupby(['locality', 'symptom_cluster']):
        group = group.sort_values('date').reset_index(drop=True)
        prior = group['case_count'].shift(1)
        group['rolling_mean'] = prior.rolling(window, min_periods=3).mean()
        group['rolling_std'] = prior.rolling(window, min_periods=3).std().replace(0, np.nan).fillna(1)
        group['z_score'] = (group['case_count'] - group['rolling_mean']) / group['rolling_std']

        anomalies = group[(group['z_score'] >= z_threshold)]
        for _, row in anomalies.iterrows():
            results.append({
                'date': row['date'].date().isoformat(),
                'locality': loc,
                'symptom_cluster': sym,
                'case_count': int(row['case_count']),
                'rolling_mean': round(float(row['rolling_mean']), 1),
                'z_score': round(float(row['z_score']), 2),
            })

    results.sort(key=lambda r: r['date'], reverse=True)
    return results
