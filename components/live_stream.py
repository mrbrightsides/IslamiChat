import streamlit as st
import requests

TV_API = "https://mp3quran.net/api/v3/live-tv?language=eng"

@st.cache_data(ttl=86400)
def fetch_tv():
    try:
        response = requests.get(TV_API)
        if response.status_code == 200:
            data = response.json()
            return data.get("radios", [])
        else:
            st.warning("Gagal mengambil data live stream. Coba lagi nanti.")
            return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def show_tv_tab():
    st.header("📺 Live Stream 24 Jam")
    st.markdown("""
        Dengarkan bacaan Al-Qur'an nonstop dengan berbagai pilihan qori internasional.  
        Sumber audio streaming dari [mp3quran.net](https://mp3quran.net).
    """)

    tv = fetch_tv()
    if not tv:
        st.info("Belum ada data live stream yang tersedia.")
        return

    # >>>> TANPA FILTER INDONESIA <<<<
    options = tv

    selected = st.selectbox(
        "Pilih qori:", 
        options, 
        format_func=lambda r: r.get("name", "TV")
    )

    stream_url = selected.get("url") or selected.get("tv_url")
    if stream_url:
        st.video(stream_url, format="video/mp4")
        st.caption(f"📺 Qori: {selected.get('name', 'Tanpa Nama')}")
    else:
        st.error("URL streaming tidak tersedia untuk channel ini.")
