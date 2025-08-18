import streamlit as st
import requests
from datetime import datetime

def render_event():
    st.header("📅 Kalender Islam")

    today = datetime.today().strftime("%Y-%m-%d")
    st.write(f"Hari ini (Masehi): `{today}`")

    # API Hijri (Aladhan)
    hijri_url = f"http://api.aladhan.com/v1/gToH?date={today}"
    resp = requests.get(hijri_url).json()

    if resp["code"] == 200:
        hijri_date = resp["data"]["hijri"]["date"]
        hijri_day = resp["data"]["hijri"]["weekday"]["ar"]
        hijri_month = resp["data"]["hijri"]["month"]["en"]
        hijri_year = resp["data"]["hijri"]["year"]

        st.success(f"Hari ini (Hijri): **{hijri_day}, {hijri_date} {hijri_month} {hijri_year} H**")

        # Tambahkan info event besar jika cocok
        event_info = check_important_event(hijri_date, hijri_month)
        if event_info:
            st.markdown(f"🌙 **Hari Besar**: {event_info}")
    else:
        st.error("Gagal memuat tanggal Hijri dari API.")

def check_important_event(day, month):
    events = {
        ("1", "Ramadan"): "Awal Ramadhan",
        ("17", "Ramadan"): "Nuzulul Qur'an",
        ("27", "Rajab"): "Isra' Mi'raj",
        ("12", "Rabi-al-awwal"): "Maulid Nabi",
        ("1", "Shawwal"): "Idul Fitri",
        ("10", "Dhu-al-Hijjah"): "Idul Adha",
    }
    return events.get((day, month))
