import datetime as dt
import pytz
import streamlit as st
import requests

# ====== Konstanta global ======
TZ = pytz.timezone("Asia/Jakarta")
METHODS = {
    "UOIF (Europe)": 12,
    "Moonsighting Committee": 20,
    "ISNA (North America)": 2,
    "Umm Al-Qura, Makkah": 4,
    "Egyptian General Authority": 5,
    "Kemenag RI (pakai Moonsighting proxy)": 20,
}

# ====== Helper functions ======
@st.cache_data(show_spinner=False, ttl=300)
def fetch_timings_by_city(city: str, country: str, method: int):
    url = "https://api.aladhan.com/v1/timingsByCity"
    r = requests.get(
        url,
        params={"city": city, "country": country, "method": method, "school": 0},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError(data)
    return data["data"]

def parse_today_times(timings_dict):
    keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    return {k: timings_dict[k] for k in keys if k in timings_dict}

def to_local_datetime(date_readable: str, time_str: str):
    d = dt.datetime.strptime(date_readable, "%d %b %Y").date()
    hh, mm = [int(x) for x in time_str.split(":")[:2]]
    naive = dt.datetime(d.year, d.month, d.day, hh, mm)
    return TZ.localize(naive)

def next_prayer(now_local: dt.datetime, times_local: dict):
    upcoming = [(name, t) for name, t in times_local.items() if t > now_local]
    if upcoming:
        return sorted(upcoming, key=lambda x: x[1])[0]
    return None, None

def fmt_delta(delta: dt.timedelta):
    s = int(delta.total_seconds())
    s = max(s, 0)
    h = s // 3600
    m = (s % 3600) // 60
    ss = s % 60
    parts = []
    if h:
        parts.append(f"{h} jam")
    if m or (h and ss):
        parts.append(f"{m} mnt")
    if h == 0:
        parts.append(f"{ss} dtk")
    return " ".join(parts)
