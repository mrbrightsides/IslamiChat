import time
import requests
import datetime as dt
import pytz
import streamlit as st
from streamlit.components.v1 import iframe

# ===== Import Komponen =====
from components.waktu_sholat import (
    TZ, METHODS, fetch_timings_by_city, parse_today_times,
    to_local_datetime, next_prayer, fmt_delta
)
from components.kiblat import show_qibla_direction
from components.zakat import zakat_kalkulator
from components.masjid import (
    get_user_location, show_nearby_mosques
)
from components.murottal import (
    RADIO_API, fetch_radios, show_murottal_tab
)
from components.event import (
    render_event, check_important_event
)
from components.khutbah_gpt import render_khutbah_form

import os
import pandas as pd  # untuk tampilan tabel lebih rapi

# ===== Page setup =====
st.set_page_config(page_title="IslamiChat 🤖🌸", layout="wide")
st.title("IslamiChat = Tanya Jawab + Waktu Sholat")
st.caption("Powered by ArtiBot / Botsonic • Waktu sholat dari Aladhan API")

from streamlit.components.v1 import iframe

# ===== Tab utama =====
tabs = st.tabs([
    "🧠 Chatbot", 
    "🕌 Waktu Sholat",
    "📻 Murottal Quran",
    "🧭 Kiblat",
    "🧮 Kalkulator Zakat",
    "🗺️ Masjid Terdekat",
    "🗓️ Event Islam",
    "🗣️ KhutbahGPT"
])

# ===== Tab: Chatbot =====
# ===== Tab: Chatbot =====
with tabs[0]:
    st.subheader("Pilih widget:")
    widget_opt = st.radio(
        " ",
        ["ArtiBot", "TawkTo"],
        horizontal=True, label_visibility="collapsed"
    )

    URLS = {
        "ArtiBot": "https://my.artibot.ai/islamichat",
        "TawkTo": "https://tawk.to/chat/63f1709c4247f20fefe15b12/1gpjhvpnb"
    }

    chosen_url = URLS[widget_opt]

    st.write(f"💬 Chat aktif: **{widget_opt}**")
    iframe(src=chosen_url, height=700)

# === Tab 1: Waktu Sholat ===
with tabs[1]:
    st.subheader("🕌 Waktu Sholat Harian")
    try:
        city = st.text_input("Kota", value="Palembang")
        country = st.text_input("Negara", value="Indonesia")
        method_name = st.selectbox("Metode perhitungan", list(METHODS.keys()), index=1)
        method = METHODS[method_name]

        payload = fetch_timings_by_city(city, country, method)
        date_readable = payload["date"]["readable"]
        timings = parse_today_times(payload["timings"])

        # Hilangkan anotasi seperti " (WIB)" jika ada
        times_local = {
            n: to_local_datetime(date_readable, t.split(" ")[0])
            for n, t in timings.items()
        }

        st.write(f"📅 **{date_readable}** — Zona: **{TZ.zone}** — Metode: **{method_name}**")
        rows = [(n, timings[n]) for n in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"] if n in timings]
        st.dataframe(pd.DataFrame(rows, columns=["Sholat", "Waktu"]), hide_index=True, use_container_width=True)

        now = dt.datetime.now(TZ)
        name, tnext = next_prayer(now, times_local)
        if name:
            st.success(f"Sholat berikutnya: **{name}** — **{tnext.strftime('%H:%M')}** (≈ {fmt_delta(tnext - now)})")
            st.caption("Hitung mundur diperbarui saat halaman di-run ulang.")
        else:
            st.info("Semua waktu sholat hari ini sudah lewat.")
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")

# === Tab 2: Murottal ===
with tabs[2]:
    show_murottal_tab()

# === Tab 3: Kiblat ===
with tabs[3]:
    show_qibla_direction()

# === Tab 4: Kalkulator Zakat ===
with tabs[4]:
    zakat_kalkulator()

# === Tab 5: Masjid Terdekat ===
with tabs[5]:
    show_nearby_mosques()

# === Tab 6: Event Islam ===
with tabs[6]:
    render_event()

# === Tab 7: KhutbahGPT ===
with tabs[7]:
    render_khutbah_form()
