import time
import requests
import datetime as dt
import pytz
import os
import pandas as pd
import streamlit as st
from streamlit.components.v1 import iframe

# ===== Komponen: Waktu Sholat =====
from components.waktu_sholat import (
    TZ, METHODS, fetch_timings_by_city, parse_today_times,
    to_local_datetime, next_prayer, fmt_delta
)

# ===== Komponen: Kiblat =====
from components.kiblat_plus import show_kiblat_tab_plus

# ===== Komponen: Zakat =====
from components.zakat import (
    zakat_kalkulator, OZT_TO_GRAM,
    fetch_gold_price_idr_per_gram, format_rp, nisab_emas_idr
)

# ===== Komponen: Masjid Terdekat =====
from components.masjid import (
    show_nearby_mosques
)

# ===== Komponen: Murottal =====
from components.murottal import (
    RADIO_API, fetch_radios, show_murottal_tab
)

# ===== Komponen: Khutbah GPT =====
from components.khutbah_gpt import (
    render_khutbah_form, generate_khutbah, generate_khutbah_gpt
)

# ===== Komponen: Live TV =====
from components.live_tv import render_live_tv_tab

# ===== Komponen: Chat Ustadz =====
from components.chat_ustadz import show_chat_ustadz_tab

# ===== Komponen: Hafalan =====
from components.tab_hafalan_audio import show_hafalan_audio_tab

# ===== Komponen: Zikir =====
from components.zikir import show_zikir_tab

# ===== Komponen: Doa Harian =====
from components.zikir import show_doa_harian

# ===== Page setup =====
st.set_page_config(page_title="IslamiChat 🤖🌸", layout="wide")
st.title("IslamiChat = Tanya Jawab + Waktu Sholat")
st.caption("Powered by ArtiBot / Botsonic • Waktu sholat dari Aladhan API")

# ===== Tab utama =====
tabs = st.tabs([
    "🧠 Chatbot", 
    "🕌 Waktu Sholat",
    "📻 Murottal Quran",
    "🧭 Kiblat",
    "🧮 Kalkulator Zakat",
    "🗺️ Masjid Terdekat",
    "🗓️ Event Islam",
    "🗣️ KhutbahGPT",
    "📺 Live TV",
    "📞 Chat Ustadz",
    "🎙️ Setor Hafalan",
    "🧿 Zikir",
    "📖 Doa Harian"
])

# ===== Tab: Chatbot =====
with tabs[0]:
    st.subheader("Pilih widget:")

    # --- Persist pilihan widget
    if "chat_widget" not in st.session_state:
        st.session_state.chat_widget = "TawkTo"  # default

    widget_opt = st.radio(
        " ", ["ArtiBot", "TawkTo"],
        horizontal=True, label_visibility="collapsed",
        index=["ArtiBot","TawkTo"].index(st.session_state.chat_widget),
        key="chat_widget"
    )

    URLS = {
        "ArtiBot": "https://my.artibot.ai/islamichat",
        "TawkTo": "https://tawk.to/chat/63f1709c4247f20fefe15b12/1gpjhvpnb"
    }
    chosen_url = URLS[widget_opt]

    # --- Opsi cache-bust (kalau iframe keliatan “nge-freeze”)
    cache_bust = st.toggle("Force refresh chat (cache-bust)", value=False)
    final_url = f"{chosen_url}?t={int(time.time())}" if cache_bust else chosen_url

    st.write(f"💬 Chat aktif: **{widget_opt}**")
    st.caption("Jika area kosong, kemungkinan dibatasi oleh CSP/X-Frame-Options dari penyedia.")

    # --- Render iframe
    iframe(src=final_url, height=720)

    # --- Fallback link aman
    st.link_button(f"↗️ Buka {widget_opt} di tab ini jika chat tidak muncul (fallback)",
                   chosen_url, use_container_width=True)

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
    show_kiblat_tab_plus()

# === Tab 4: Kalkulator Zakat ===
with tabs[4]:
    zakat_kalkulator()

# === Tab 5: Masjid Terdekat ===
with tabs[5]:
    show_nearby_mosques()

# === Tab 6: Event Islam ===
with tabs[6]:
    try:
        from components.event import render_event
        render_event()
    except Exception as e:
        st.warning(f"Gagal memuat kalender lengkap: {e}. Menampilkan kalender sederhana.")
        from components.event import render_simple_hijri_calendar
        render_simple_hijri_calendar()

# === Tab 7: KhutbahGPT ===
with tabs[7]:
    render_khutbah_form()

# === Tab 8: Live TV ===
with tabs[8]:
    render_live_tv_tab()

# === Tab 9: Chat Ustadz ===
with tabs[9]:
    show_chat_ustadz_tab()

# === Tab 10: Hafalan ===
with tabs[10]:
    show_hafalan_audio_tab()

# === Tab 11: Zikir ===
with tabs[11]:
    show_zikir_tab()

# === Tab 12: Doa Harian ===
with tabs[12]:
    show_doa_harian()
