import json
import os
from datetime import datetime, timezone

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'actions_log.json')


def _load_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            return json.load(f)
    return []


def _save_log(log):
    with open(LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)


def _record_action(action_type, details):
    log = _load_log()
    entry = {
        'action_id': f'ACT{len(log)+1:04d}',
        'action_type': action_type,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': details,
    }
    log.append(entry)
    _save_log(log)
    return entry


def evaluate_outbreak_response(anomalies):
    triggered = []
    counts = {}
    for a in anomalies:
        key = (a['locality'], a['symptom_cluster'])
        counts[key] = counts.get(key, 0) + 1

    for (locality, symptom), n in counts.items():
        if n >= 2:
            action = _record_action('OUTBREAK_RESPONSE', {
                'locality': locality,
                'symptom_cluster': symptom,
                'anomaly_count': n,
                'response': [
                    'Dispatch community health worker team for door-to-door inspection',
                    'Schedule fogging / sanitation operation within 48 hours',
                    'Publish public health advisory for the locality',
                ],
            })
            triggered.append(action)
    return triggered


def evaluate_case_triage(risk_level: str, locality: str, patient_ref: str, notes: str = ''):
    risk_level = risk_level.lower()
    if risk_level == 'high':
        return _record_action('SAME_DAY_REFERRAL', {
            'locality': locality, 'patient_ref': patient_ref, 'notes': notes,
            'sla': 'Refer within 4 hours', 'notified': 'nearest available clinic',
        })
    elif risk_level == 'moderate':
        return _record_action('FOLLOWUP_REMINDER', {
            'locality': locality, 'patient_ref': patient_ref, 'notes': notes,
            'sla': 'Follow up within 48 hours',
        })
    else:
        return _record_action('LOGGED_LOW_RISK', {
            'locality': locality, 'patient_ref': patient_ref, 'notes': notes,
        })


def get_action_log():
    return list(reversed(_load_log()))
