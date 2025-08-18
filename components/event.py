import streamlit as st
import requests
from datetime import datetime
from typing import Optional

API_G_TO_H = "https://api.aladhan.com/v1/gToH"

@st.cache_data(ttl=6 * 60 * 60)
def g_to_h(date_dd_mm_yyyy: str) -> Optional[dict]:
    """Konversi Gregorian → Hijri. Param harus DD-MM-YYYY sesuai dok Aladhan."""
    try:
        r = requests.get(API_G_TO_H, params={"date": date_dd_mm_yyyy}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 200 and "data" in data and "hijri" in data["data"]:
            return data["data"]["hijri"]
        # fallback: beberapa response lama meletakkan kunci langsung di 'data'
        if data.get("code") == 200 and isinstance(data.get("data"), dict):
            return data["data"]
    except Exception as e:
        st.error(f"Gagal memuat tanggal Hijriah: {e}")
    return None

def check_important_event(hijri_day: int, hijri_month_num: int) -> Optional[str]:
    EVENTS = {
        (1, 9):  "Awal Ramadhan",
        (17, 9): "Nuzulul Qur'an",
        (27, 7): "Isra' Mi'raj",
        (12, 3): "Maulid Nabi",
        (1, 10): "Idul Fitri",
        (10, 12): "Idul Adha",
    }
    return EVENTS.get((hijri_day, hijri_month_num))

def render_event():
    st.header("📅 Kalender Islam")

    # Tampilkan tanggal Masehi (YYYY-MM-DD) hanya untuk display
    today_display = datetime.today().strftime("%Y-%m-%d")
    st.write(f"Hari ini (Masehi): `{today_display}`")

    # Format yang benar untuk API: DD-MM-YYYY
    today_for_api = datetime.today().strftime("%d-%m-%Y")

    hijri = g_to_h(today_for_api)
    if not hijri:
        st.error("Tidak bisa mendapatkan konversi Hijriah dari API.")
        return

    try:
        h_day = int(hijri["day"])
        h_month_num = int(hijri["month"]["number"])
        h_month_en = hijri["month"]["en"]
        h_weekday_ar = hijri["weekday"]["ar"]
        h_date_str = hijri["date"]  # biasanya dd-mm-yyyy (Hijri)
    except Exception as e:
        st.error(f"Format data Hijriah tak terduga: {e}")
        return

    st.success(f"Hari ini (Hijri): **{h_weekday_ar}, {h_date_str} {h_month_en} H**")

    event_info = check_important_event(h_day, h_month_num)
    if event_info:
        st.markdown(f"🌙 **Hari Besar**: {event_info}")
    else:
        st.caption("Belum ada hari besar yang bertepatan hari ini.")
