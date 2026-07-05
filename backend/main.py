from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_loader import load_clinics, load_daily_cases, load_helpline
from rag import KnowledgeBase, generate_answer
from anomaly import detect_anomalies
from forecast import forecast_series
from workflow_ageny import evaluate_outbreak_response, evaluate_case_triage, get_action_log

app = FastAPI(title='CommunityPulse API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

kb = KnowledgeBase()
clinics_df = load_clinics()
cases_df = load_daily_cases()
helpline_df = load_helpline()


class AskRequest(BaseModel):
    question: str
    locality: str | None = None


class TriageRequest(BaseModel):
    risk_level: str
    locality: str
    patient_ref: str
    notes: str = ''


@app.get('/')
def root():
    return {
        'name': 'CommunityPulse API',
        'version': '0.1.0',
        'status': 'ok',
        'endpoints': ['/health', '/ask', '/analytics/summary', '/analytics/forecast'],
    }


@app.post('/ask')
def ask(req: AskRequest):
    live_context = ''
    if req.locality:
        recent = cases_df[cases_df['locality'] == req.locality]
        recent7 = recent[recent['date'] >= recent['date'].max() - pd_days(7)]
        by_symptom = recent7.groupby('symptom_cluster')['case_count'].sum().to_dict()
        if by_symptom:
            summary = ', '.join(f"{k.replace('_', ' ')}: {v} cases" for k, v in by_symptom.items())
            live_context = f"Live data for {req.locality} (last 7 days) — {summary}."

    result = generate_answer(kb, req.question, live_context=live_context)
    return result


def pd_days(n):
    import pandas as pd
    return pd.Timedelta(days=n)


@app.get('/analytics/summary')
def analytics_summary():
    total_cases = int(cases_df['case_count'].sum())
    by_locality = cases_df.groupby('locality')['case_count'].sum().sort_values(ascending=False).to_dict()
    by_symptom = cases_df.groupby('symptom_cluster')['case_count'].sum().sort_values(ascending=False).to_dict()
    calls_by_category = helpline_df.groupby('category').size().sort_values(ascending=False).to_dict()
    return {
        'total_cases_35_days': total_cases,
        'cases_by_locality': by_locality,
        'cases_by_symptom': by_symptom,
        'helpline_calls_by_category': calls_by_category,
        'clinics': clinics_df.to_dict(orient='records'),
    }


@app.get('/analytics/timeseries')
def analytics_timeseries(locality: str = Query(...), symptom_cluster: str = Query(...)):
    subset = cases_df[
        (cases_df['locality'] == locality) & (cases_df['symptom_cluster'] == symptom_cluster)
    ].sort_values('date')
    return [
        {'date': row['date'].date().isoformat(), 'case_count': int(row['case_count'])}
        for _, row in subset.iterrows()
    ]


@app.get('/analytics/anomalies')
def analytics_anomalies():
    anomalies = detect_anomalies(cases_df)
    return {'count': len(anomalies), 'anomalies': anomalies}


@app.get('/analytics/forecast')
def analytics_forecast(locality: str = Query(...), symptom_cluster: str = Query(...), horizon: int = 7):
    return forecast_series(cases_df, locality, symptom_cluster, horizon=horizon)


@app.post('/workflows/run-outbreak-check')
def run_outbreak_check():
    anomalies = detect_anomalies(cases_df)
    triggered = evaluate_outbreak_response(anomalies)
    return {'anomalies_considered': len(anomalies), 'actions_triggered': triggered}


@app.post('/workflows/triage')
def triage(req: TriageRequest):
    action = evaluate_case_triage(req.risk_level, req.locality, req.patient_ref, req.notes)
    return action


@app.get('/workflows/actions')
def list_actions():
    return get_action_log()


@app.get('/health')
def health():
    return {'status': 'ok'}
