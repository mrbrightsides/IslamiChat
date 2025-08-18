import streamlit as st
import requests
from datetime import datetime
from typing import Optional

API_G_TO_H = "https://api.aladhan.com/v1/gToH"

# ===== Cache converter =====
@st.cache_data(ttl=6 * 60 * 60)  # cache 6 jam
def g_to_h(greg_date_yyyy_mm_dd: str) -> Optional[dict]:
    try:
        r = requests.get(API_G_TO_H, params={"date": greg_date_yyyy_mm_dd}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("code") == 200 and "data" in data:
            return data["data"]["hijri"]  # dict hijri
    except Exception as e:
        st.error(f"Gagal memuat tanggal Hijriah: {e}")
    return None

def check_important_event(hijri_day: int, hijri_month_num: int) -> Optional[str]:
    """
    hijri_month_num: 1..12 (1=Muharram, 7=Rajab, 9=Ramadan, 10=Shawwal, 12=Dhu al-Hijjah)
    """
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

    today_g = datetime.today().strftime("%Y-%m-%d")
    st.write(f"Hari ini (Masehi): `{today_g}`")

    hijri = g_to_h(today_g)
    if not hijri:
        st.error("Tidak bisa mendapatkan konversi Hijriah dari API.")
        return

    # contoh struktur hijri (Aladhan):
    # {"date":"08-07-1445","day":"8","month":{"number":7,"en":"Rajab","ar":"رجب"}, "weekday":{"ar":"الخميس","en":"Thursday"}, ...}
    try:
        h_day = int(hijri["day"])
        h_month_num = int(hijri["month"]["number"])
        h_month_en = hijri["month"]["en"]
        h_weekday_ar = hijri["weekday"]["ar"]
        h_date_str = hijri["date"]  # dd-mm-yyyy (Hijri)
    except Exception as e:
        st.error(f"Format data Hijriah tak terduga: {e}")
        return

    st.success(f"Hari ini (Hijri): **{h_weekday_ar}, {h_date_str} {h_month_en} H**")

    event_info = check_important_event(h_day, h_month_num)
    if event_info:
        st.markdown(f"🌙 **Hari Besar**: {event_info}")
    else:
        st.caption("Belum ada hari besar yang bertepatan hari ini.")
