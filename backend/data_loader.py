import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _read_csv(filename, **kwargs):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def load_clinics():
    return _read_csv("clinics.csv")


def load_daily_cases():
    return _read_csv("daily_cases.csv", parse_dates=["date"])


def load_helpline():
    return _read_csv("helpline_complaints.csv", parse_dates=["date"])
