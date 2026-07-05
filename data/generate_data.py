"""
Generates synthetic-but-realistic datasets for the CommunityPulse demo:
  - clinics.csv            : clinic directory with location & capacity
  - daily_cases.csv        : daily symptom-cluster case counts per locality (with an injected outbreak)
  - helpline_complaints.csv: citizen helpline call log (locality, category, sentiment)

In production these would be replaced by real EHR / helpline / IoT feeds
ingested via Pub/Sub + Dataflow into BigQuery / AlloyDB.
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

LOCALITIES = ["Rajajinagar", "Whitefield", "Koramangala", "Yelahanka"]
SYMPTOMS = ["fever", "respiratory", "dengue_like", "gastro"]

# ---------------- clinics.csv ----------------
clinics = [
    ("CLN001", "Rajajinagar PHC",  "Rajajinagar", 40, "General"),
    ("CLN002", "Whitefield Urban Clinic", "Whitefield", 60, "General"),
    ("CLN003", "Koramangala Community Health Centre", "Koramangala", 50, "General"),
    ("CLN004", "Yelahanka Rural Clinic", "Yelahanka", 25, "General"),
    ("CLN005", "Rajajinagar Maternity Clinic", "Rajajinagar", 20, "Maternal Care"),
    ("CLN006", "Koramangala Vaccination Camp", "Koramangala", 100, "Vaccination"),
]
with open("clinics.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["clinic_id", "clinic_name", "locality", "daily_capacity", "clinic_type"])
    w.writerows(clinics)

# ---------------- daily_cases.csv ----------------
START = date(2026, 6, 1)
DAYS = 35
rows = [["date", "locality", "symptom_cluster", "case_count"]]

for d in range(DAYS):
    day = START + timedelta(days=d)
    for loc in LOCALITIES:
        for sym in SYMPTOMS:
            base = {
                "fever": 8, "respiratory": 6, "dengue_like": 3, "gastro": 4
            }[sym]
            noise = random.randint(-2, 3)
            count = max(0, base + noise)

            # Inject a dengue-like outbreak in Koramangala starting day 22
            if loc == "Koramangala" and sym == "dengue_like" and d >= 22:
                growth = (d - 21) * 2
                count += growth + random.randint(0, 2)

            # Inject a respiratory spike in Whitefield around day 15-18 (short-lived)
            if loc == "Whitefield" and sym == "respiratory" and 15 <= d <= 19:
                count += 10 + random.randint(0, 3)

            rows.append([day.isoformat(), loc, sym, count])

with open("daily_cases.csv", "w", newline="") as f:
    csv.writer(f).writerows(rows)

# ---------------- helpline_complaints.csv ----------------
categories = ["appointment_help", "symptom_query", "scheme_eligibility",
              "medicine_availability", "clinic_wait_time", "vaccination_info"]
sentiments = ["neutral", "frustrated", "worried", "satisfied"]

complaint_rows = [["call_id", "date", "locality", "category", "sentiment", "notes"]]
call_id = 1
for d in range(DAYS):
    day = START + timedelta(days=d)
    n_calls = random.randint(8, 16)
    for _ in range(n_calls):
        loc = random.choice(LOCALITIES)
        cat = random.choice(categories)
        sent = random.choice(sentiments)
        # more "worried" + symptom_query calls in Koramangala during the outbreak window
        if loc == "Koramangala" and d >= 23:
            cat = random.choice(["symptom_query", "symptom_query", "clinic_wait_time"])
            sent = random.choice(["worried", "frustrated"])
        note_map = {
            "appointment_help": "Caller requested help booking a clinic appointment.",
            "symptom_query": "Caller described fever/body-ache symptoms and asked for guidance.",
            "scheme_eligibility": "Caller asked about eligibility for a government health scheme.",
            "medicine_availability": "Caller asked whether a medicine is in stock nearby.",
            "clinic_wait_time": "Caller complained about long wait times at the clinic.",
            "vaccination_info": "Caller asked about upcoming vaccination camp schedule.",
        }
        complaint_rows.append([call_id, day.isoformat(), loc, cat, sent, note_map[cat]])
        call_id += 1

with open("helpline_complaints.csv", "w", newline="") as f:
    csv.writer(f).writerows(complaint_rows)

print(f"Generated: clinics.csv ({len(clinics)} rows), "
      f"daily_cases.csv ({len(rows)-1} rows), "
      f"helpline_complaints.csv ({len(complaint_rows)-1} rows)")