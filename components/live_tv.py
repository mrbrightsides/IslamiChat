import requests
import streamlit as st

API_URL = "https://mp3quran.net/api/v3/live-tv?language=eng"

# ---------- Fetch & parsing ----------
@st.cache_data(ttl=30 * 60, show_spinner=False)
def fetch_live_tv():
    r = requests.get(API_URL, timeout=20, headers={"User-Agent": "IslamiChat/1.0"})
    r.raise_for_status()
    return r.json()

def _flatten_items(payload: dict) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    for key in ("live_tvs", "live", "data", "result", "channels"):
        v = payload.get(key)
        if isinstance(v, list) and v:
            return [x for x in v if isinstance(x, dict)]
    return []

def _pick_title(item: dict) -> str:
    return (item.get("name")
            or item.get("title")
            or item.get("channel")
            or "Live Channel")

def _pick_url(item: dict) -> str | None:
    # cari kandidat url stream
    cands = [
        item.get("hls"), item.get("m3u8"), item.get("hls_url"),
        item.get("stream_url"), item.get("url"), item.get("link")
    ]
    src = item.get("source") or item.get("urls")
    if isinstance(src, dict):
        cands += [src.get("hls"), src.get("url"), src.get("link")]
    elif isinstance(src, list):
        for x in src:
            if isinstance(x, dict):
                cands += [x.get("hls"), x.get("url"), x.get("link")]
    for u in cands:
        if isinstance(u, str) and u.startswith(("http://", "https://")):
            return u
    return None

def _loc_tag(txt: str) -> str:
    t = (txt or "").lower()
    if any(k in t for k in ["madinah", "medina", "nabawi"]): return "Madinah"
    if any(k in t for k in ["makkah", "mecca", "haram"]):   return "Makkah"
    return "Lainnya"

def extract_channels(payload: dict) -> list[dict]:
    out = []
    for it in _flatten_items(payload):
        url = _pick_url(it)
        if not url:
            continue
        title = _pick_title(it)
        out.append({
            "title": title,
            "tag": _loc_tag(f"{title} {it.get('description','')}"),
            "url": url,
            "raw": it
        })
    return out

# ---------- UI helpers ----------
def _player(url: str):
    # st.video bisa mainkan YouTube & HLS .m3u8
    st.video(url)
    with st.expander("Jika player tidak muncul, coba fallback HTML"):
        st.markdown(
            f"""
            <video width="100%" height="auto" controls autoplay playsinline>
              <source src="{url}" type="application/vnd.apple.mpegurl">
              <source src="{url}">
              Browser kamu tidak mendukung pemutaran video ini.
            </video>
            """,
            unsafe_allow_html=True
        )

# ---------- Main render ----------
def render_live_tv_tab():
    st.subheader("📺 Live TV — Makkah & Madinah")
    st.caption("Akan mencoba sumber API mp3quran terlebih dahulu; jika tidak tersedia, pakai YouTube/custom link.")

    col1, col2 = st.columns([1, 2])
    with col1:
        prefer = st.radio(
            "Sumber",
            ["Auto (API ➜ fallback)", "YouTube / Custom"],
            index=0
        )
    with col2:
        quick = st.radio("Filter lokasi (untuk API)", ["Semua", "Makkah", "Madinah"], horizontal=True)

    channels = []
    api_error = None

    if prefer.startswith("Auto"):
        try:
            data = fetch_live_tv()
            channels = extract_channels(data)
        except Exception as e:
            api_error = str(e)

    # --- jika API sukses dan ada data ---
    if prefer.startswith("Auto") and channels:
        # filter
        if quick != "Semua":
            channels = [c for c in channels if c["tag"] == quick]

        if not channels:
            st.info("Tidak ada channel cocok untuk filter saat ini.")
            return

        idx = st.selectbox(
            "Pilih channel (API)",
            options=list(range(len(channels))),
            format_func=lambda i: f"{channels[i]['title']} — {channels[i]['tag']}"
        )
        chosen = channels[idx]
        st.success(f"Memutar (API): **{chosen['title']}** · **{chosen['tag']}**")
        _player(chosen["url"])

        with st.expander("Detail mentah (debug)"):
            st.json(chosen["raw"])
        return

    # --- fallback YouTube/custom (atau manual pilih YouTube) ---
    if api_error and prefer.startswith("Auto"):
        st.warning(f"Sumber API tidak tersedia: {api_error}\nBerpindah ke YouTube/Custom.")

    st.markdown("### YouTube / Custom Link")
    st.caption("Isi URL live dari YouTube (watch/embed) atau link HLS `.m3u8`.")

    # Simpan isian agar enak dipakai ulang
    if "live_links" not in st.session_state:
        st.session_state.live_links = {
            "Makkah": "",
            "Madinah": "",
        }

    choice = st.radio("Channel", ["Makkah", "Madinah"], horizontal=True)
    url = st.text_input(
        f"URL {choice}",
        value=st.session_state.live_links.get(choice, ""),
        placeholder="contoh: https://www.youtube.com/watch?v=XXXXXXXXX  atau  https://.../stream.m3u8"
    )
    st.session_state.live_links[choice] = url

    if not url:
        st.info("Tempelkan URL live YouTube / m3u8 di atas, lalu video akan muncul di sini.")
        return

    st.success(f"Memutar (YouTube/Custom): **{choice}**")
    _player(url)
