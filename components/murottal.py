import streamlit as st
import requests

RADIO_API = "http://api.mp3quran.net/radios/get_radios.php"

@st.cache_data(ttl=86400)
def fetch_radios():
    try:
        response = requests.get(RADIO_API)
        if response.status_code == 200:
            data = response.json()
            return data.get("radios", [])
        else:
            st.warning("Gagal mengambil data radio. Coba lagi nanti.")
            return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def show_murottal_tab():
    st.header("📻 Murottal 24 Jam")
    st.markdown("""
        Dengarkan bacaan Al-Qur'an nonstop yang disertai terjemahan Bahasa Indonesia.
        Sumber audio streaming dari [mp3quran.net](https://mp3quran.net).
    """)

    radios = fetch_radios()
    if not radios:
        st.info("Belum ada data radio yang tersedia.")
        return

    # Filter radio berbahasa Indonesia
    indo_radios = [r for r in radios if "indonesia" in r.get("name", "").lower()]

    if not indo_radios:
        st.warning("Radio berbahasa Indonesia tidak ditemukan. Menampilkan semua radio.")
        options = radios
    else:
        options = indo_radios

    selected = st.selectbox("Pilih channel radio:", options, format_func=lambda r: r.get("name", "Radio"))

    stream_url = selected.get("url")
    if stream_url:
        st.audio(stream_url, format="audio/mp3")
        st.caption(f"Siaran: {selected.get('name', 'Tanpa Nama')}")
    else:
        st.error("URL streaming tidak tersedia untuk channel ini.")
