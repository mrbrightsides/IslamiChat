import streamlit as st
import requests

API_BASE = "https://mp3quran.net/api/v3/radios"

def _fetch_radios(lang="eng") -> list:
    """Ambil daftar radio dari mp3quran v3. Raise error kalau gagal (agar tidak tercache)."""
    url = f"{API_BASE}?language={lang}"
    r = requests.get(url, timeout=10, headers={"User-Agent": "IslamiChat/1.0"})
    r.raise_for_status()
    data = r.json() or {}
    return data.get("radios", [])

@st.cache_data(ttl=3600)  # cache 1 jam, hanya untuk hasil sukses
def fetch_radios(lang="eng"):
    radios = _fetch_radios(lang)
    # kalau kosong di lang tertentu, fallback ke english
    if not radios and lang != "eng":
        radios = _fetch_radios("eng")
    return radios

def show_murottal_tab():
    st.header("📻 Murottal 24 Jam")
    st.markdown(
        "Dengarkan bacaan Al-Qur'an nonstop yang disertai terjemahan. "
        "Sumber audio streaming: mp3quran.net."
    )

    colA, colB = st.columns([1,1])
    with colA:
        lang = st.selectbox("Bahasa daftar channel (untuk metadata):", ["eng", "ar"], index=0)
    with colB:
        if st.button("🔄 Reload daftar radio", use_container_width=True):
            fetch_radios.clear()  # clear cache data

    try:
        radios = fetch_radios(lang=lang)
    except Exception as e:
        st.error(f"Gagal mengambil data radio: {e}")
        st.info("Coba klik **Reload daftar radio** di atas.")
        return

    if not radios:
        st.info("Belum ada data radio yang tersedia dari API.")
        return

    # Filter radio 'Indonesia' dari nama (kadang provider menulis 'Indonesia' / 'Indonesian')
    keywords = ("indonesia", "indonesian", "bahasa indonesia")
    indo_radios = [r for r in radios if any(k in r.get("name","").lower() for k in keywords)]
    options = indo_radios if indo_radios else radios

    selected = st.selectbox(
        "Pilih channel radio:",
        options,
        format_func=lambda r: r.get("name", "Radio")
    )

    stream_url = selected.get("url") or selected.get("radio_url")  # jaga-jaga variasi field
    if stream_url:
        st.audio(stream_url, format="audio/mp3")
        st.caption(f"Siaran: {selected.get('name','Tanpa Nama')}")
    else:
        st.error("URL streaming tidak tersedia untuk channel ini.")

    # Debug opsional
    if st.toggle("Tampilkan data mentah (debug)", value=False):
        st.write(f"Total radios: {len(radios)} | Indonesia-match: {len(indo_radios)}")
        st.json(radios[:5])
