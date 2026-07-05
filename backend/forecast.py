import pandas as pd
import numpy as np


def forecast_series(df: pd.DataFrame, locality: str, symptom_cluster: str, horizon=7, alpha=0.4):
    subset = df[(df['locality'] == locality) & (df['symptom_cluster'] == symptom_cluster)]
    subset = subset.sort_values('date')
    values = subset['case_count'].to_numpy(dtype=float)
    dates = subset['date'].tolist()

    if len(values) < 5:
        return {'error': 'not enough history for this locality/symptom combination'}

    level = values[0]
    smoothed = [level]
    for v in values[1:]:
        level = alpha * v + (1 - alpha) * level
        smoothed.append(level)

    recent = values[-7:]
    trend = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)

    last_date = dates[-1]
    last_level = smoothed[-1]
    forecast = []
    for i in range(1, horizon + 1):
        f_date = last_date + pd.Timedelta(days=i)
        f_value = max(0, last_level + trend * i)
        forecast.append({'date': f_date.date().isoformat(), 'forecast': round(float(f_value), 1)})

    return {
        'locality': locality,
        'symptom_cluster': symptom_cluster,
        'recent_trend_per_day': round(float(trend), 2),
        'forecast': forecast,
    }
