# components/live_tv.py
import re
import json
import time
import requests
import streamlit as st

API_URL = "https://mp3quran.net/api/v3/live-tv?language=eng"

@st.cache_data(ttl=60 * 30, show_spinner=False)
def fetch_live_tv_json():
    """Ambil data Live TV dari mp3quran (cache 30 menit)."""
    headers = {"User-Agent": "IslamiChat/1.0 (+streamlit)"}
    r = requests.get(API_URL, headers=headers, timeout=20)
    r.raise_for_status()
    return r.json()

def _lower(s: str) -> str:
    return (s or "").strip().lower()

def _pick_url(item: dict) -> str | None:
    """
    Ambil url streaming dari berbagai kemungkinan field.
    Banyak API HLS menggunakan .m3u8, Streamlit mendukung st.video() untuk HLS.
    """
    candidates = [
        item.get("hls"),
        item.get("hls_url"),
        item.get("stream_url"),
        item.get("url"),
        item.get("link"),
        item.get("m3u8"),
    ]

    # Kadang nested di item["source"] / item["urls"]
    src = item.get("source") or item.get("urls")
    if isinstance(src, dict):
        candidates.append(src.get("hls") or src.get("url") or src.get("link"))
    elif isinstance(src, list):
        for x in src:
            if isinstance(x, dict):
                candidates.append(x.get("hls") or x.get("url") or x.get("link"))

    # pilih yang terlihat valid
    for u in candidates:
        if isinstance(u, str) and u.startswith(("http://", "https://")):
            return u
    return None

def _title(item: dict) -> str:
    name = item.get("name") or item.get("title") or item.get("channel") or "Live Channel"
    # kadang ada name_translated / name_en
    name_en = item.get("name_en") or item.get("english_name")
    if name_en and _lower(name_en) != _lower(name):
        return f"{name} ({name_en})"
    return str(name)

def _location_tag(item: dict) -> str:
    """Deteksi mekkah/madinah dari teks nama/desc."""
    txt = " ".join(
        str(x or "")
        for x in [
            item.get("name"),
            item.get("name_en"),
            item.get("title"),
            item.get("description"),
        ]
    )
    t = _lower(txt)
    if any(k in t for k in ["madinah", "medina", "al-madinah"]):
        return "Madinah"
    if any(k in t for k in ["makkah", "mecca", "al-masjid al-haram", "masjid al-haram"]):
        return "Makkah"
    return "Lainnya"

def _flatten_items(payload: dict) -> list[dict]:
    """
    API mp3quran biasanya punya root 'live' atau 'live_tvs'.
    Kita normalisasi biar aman.
    """
    if not isinstance(payload, dict):
        return []
    for key in ["live_tvs", "live", "data", "result", "channels"]:
        val = payload.get(key)
        if isinstance(val, list) and val:
            return [x for x in val if isinstance(x, dict)]
    # fallback: kalau payload sendiri sudah berisi item tunggal
    return [payload] if payload else []

def _extract_channels(payload: dict) -> list[dict]:
    items = _flatten_items(payload)
    channels = []
    for it in items:
        url = _pick_url(it)
        if not url:
            continue
        channels.append(
            {
                "title": _title(it),
                "url": url,
                "tag": _location_tag(it),
                "raw": it,
            }
        )
    return channels

def _render_player(url: str):
    """
    Tampilkan player. st.video mendukung HLS (.m3u8).
    Jika ada CSP/blocked, sediakan fallback HTML video tag.
    """
    st.video(url)
    with st.expander("Jika player tidak muncul, coba fallback HTML", expanded=False):
        st.markdown(
            f"""
            <video width="100%" height="auto" controls autoplay playsinline>
                <source src="{url}" type="application/vnd.apple.mpegurl">
                <source src="{url}" type="video/mp4">
                Browser kamu tidak mendukung pemutaran video live ini.
            </video>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Catatan: beberapa perangkat memerlukan klik Play manual untuk live stream.")

def render_live_tv_tab():
    st.subheader("📺 Live TV — Makkah & Madinah")
    st.caption("Sumber: mp3quran.net — endpoint live TV")

    # Controls
    colA, colB, colC = st.columns([1, 2, 2])
    with colA:
        refresh = st.button("↻ Muat Ulang", use_container_width=True)
    with colB:
        quick = st.radio("Filter cepat", ["Semua", "Makkah", "Madinah"], horizontal=True)
    with colC:
        query = st.text_input("Cari channel", placeholder="mis. haram, prophet, quran", label_visibility="visible")

    # Fetch data
    try:
        data = fetch_live_tv_json() if not refresh else fetch_live_tv_json.clear() or fetch_live_tv_json()
        chans = _extract_channels(data)
    except Exception as e:
        st.error(f"Gagal memuat data live TV: {e}")
        st.stop()

    if not chans:
        st.warning("Tidak ada channel ditemukan dari API saat ini.")
        st.stop()

    # Apply filter
    def _match(c):
        if quick != "Semua" and c["tag"] != quick:
            return False
        if query and _lower(query) not in _lower(c["title"]):
            return False
        return True

    filtered = [c for c in chans if _match(c)]
    if not filtered:
        st.info("Tidak ada channel yang cocok dengan filter saat ini.")
        st.stop()

    # Pilihan channel
    titles = [f"{c['title']} — {c['tag']}" for c in filtered]
    idx = st.selectbox("Pilih channel", options=list(range(len(filtered))), format_func=lambda i: titles[i])

    # Render player
    chosen = filtered[idx]
    st.success(f"Memutar: **{chosen['title']}**  ·  Lokasi: **{chosen['tag']}**")
    _render_player(chosen["url"])

    with st.expander("Detail mentah (debug)"):
        st.json(chosen["raw"])
