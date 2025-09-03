import time
import requests
import datetime as dt
import pytz
import os
import pandas as pd
import streamlit as st
from streamlit.components.v1 import iframe

if st.query_params.get("ping") == "1":
    st.write("ok"); st.stop()

# ===== Komponen: Waktu Sholat =====
from components.waktu_sholat import (
    TZ, METHODS, fetch_timings_by_city, parse_today_times,
    to_local_datetime, next_prayer, fmt_delta
)

# ===== Komponen: Quran =====
from components.quran import render_quran_tab

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
from components.doa_harian import show_doa_harian

# ===== Page setup =====
st.set_page_config(
    page_title="SmartFaith",
    page_icon="🕋",
    layout="wide"
)

LOGO_URL = "https://i.imgur.com/vPQigu6.png"

col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_URL, use_container_width=True)
with col2:
    st.markdown("""
        ## SmartFaith 🕌
    """)

st.caption("Asisten Islami Berbasis AI: Tanya Jawab, Generator Khutbah, & Setor Hafalan")

# ===== Tab utama =====
tabs = st.tabs([
    "🤖 Chatbot", 
    "🕌 Waktu Sholat",
    "📻 Murottal Quran",
    "📖 Quran",
    "🧮 Kalkulator Zakat",
    "🗺️ Masjid Terdekat",
    "🗓️ Event Islam",
    "🗣️ KhutbahGPT",
    "📺 Live TV",
    "📞 Chat Ustadz",
    "🎙️ Setor Hafalan",
    "🧿 Zikir",
    "📚 Doa Harian"
])

# ===== Tab: Chatbot =====
with tabs[0]:
    st.subheader("🤖 Chatbot Islami")
    st.markdown("""
        Silakan pilih beragam pilihan widget chatbot sesuai kebutuhan Anda:
    """)

    # --- Persist pilihan widget
    if "chat_widget" not in st.session_state:
        st.session_state.chat_widget = "TawkTo"  # default

    widget_opt = st.radio(
        " ", ["ArtiBot", "TawkTo", "ChatBase", "Botsonic", "Denser", "Cortex"],
        horizontal=True, label_visibility="collapsed",
        index=["ArtiBot","TawkTo","ChatBase","Botsonic","Denser","Cortex"].index(st.session_state.chat_widget),
        key="chat_widget"
    )

    URLS = {
        "ArtiBot": "https://my.artibot.ai/islamichat",
        "TawkTo": "https://tawk.to/chat/63f1709c4247f20fefe15b12/1gpjhvpnb",
        "ChatBase": "https://www.chatbase.co/chatbot-iframe/Ho6CMtS7y0t5oM-Ktx9jU",
        "Botsonic": "https://bot.writesonic.com/share/bot/a148b878-259e-4591-858a-8869b9b23604",
        "Denser": "https://denser.ai/u/embed/chatbot_pbix8pdjxk9brvund1afv",
        "Cortex": "https://zenoembed.textcortex.com/?embed_id=emb_01k489emhkefvvsnhpxpqjtc7s"
    }
    chosen_url = URLS[widget_opt]

    cache_bust = st.toggle("Force refresh chat (cache-bust)", value=False)
    final_url = f"{chosen_url}?t={int(time.time())}" if cache_bust else chosen_url

    st.write(f"💬 Chat aktif: **{widget_opt}**")
    st.caption("Jika area kosong, kemungkinan dibatasi oleh CSP/X-Frame-Options dari penyedia.")

    iframe(src=final_url, height=720)

    if st.button(f"🔗 Klik disini jika ingin menampilkan halaman chat {widget_opt} dengan lebih baik"):
        st.markdown(
            f"""
            <meta http-equiv="refresh" content="0; url={chosen_url}">
            """,
            unsafe_allow_html=True
        )

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

# === Tab 3: Quran ===
with tabs[3]:
    render_quran_tab()

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
