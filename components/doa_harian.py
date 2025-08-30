import requests
import streamlit as st
from typing import Any, Dict, List, Optional

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60  # 1 jam

# ---------- helpers ----------
def _getv(d: Dict[str, Any], *candidates: str, default: str = "") -> str:
    """Ambil d[k] dengan beberapa fallback nama kunci."""
    for k in candidates:
        if k in d and d[k] is not None:
            v = d[k]
            return str(v)
    return default

def _normalize_container(raw: Any) -> List[Dict[str, Any]]:
    """Jika respons dibungkus 'data' atau 'result', ambil isinya."""
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("result") or raw.get("items") or []
    return raw if isinstance(raw, list) else []

def _normalize_item(x: Dict[str, Any]) -> Dict[str, Any]:
    """Samakan nama kunci dari berbagai kemungkinan API (EQuran.id, dsb)."""
    _id   = _getv(x, "id", "ID", "no", default="")
    judul = _getv(
        x, "nama", "doa", "title", "judul",  # <— tambahkan "nama"
        default=f"Tanpa judul #{_id or '?'}"
    )
    arab  = _getv(
        x, "ar", "ayat", "arab", "arabic", "arab_text"  # <— tambahkan "ar"
    )
    latin = _getv(
        x, "tr", "latin", "transliterasi", "latin_text"  # <— tambahkan "tr"
    )
    indo  = _getv(
        x, "idn", "artinya", "indo", "translation", "terjemahan", "id"  # <— tambahkan "idn"
    )
    grup  = _getv(x, "grup", "group", "kategori", default="Tanpa Grup")
    ref   = _getv(x, "tentang", "sumber", "reference", default="")
    tags  = x.get("tag") or x.get("tags") or []

    return {
        "id": _id,
        "grup": grup,
        "judul": judul,
        "arab": arab,
        "latin": latin,
        "indo": indo,
        "ref": ref,
        "tags": tags,
    }

# ---------- fetchers ----------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_list(grup: Optional[str] = None, tag: Optional[str] = None, debug: bool = False) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    items = _normalize_container(raw)
    out: List[Dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            out.append(_normalize_item(it))

    # (opsional) tampilkan dump jika mau debugging cepat
    if debug:
        st.caption("Debug: respons mentah daftar")
        st.json(raw)

    return out

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_detail(doa_id: str, debug: bool = False) -> Dict[str, Any]:
    if not doa_id:
        return {}
    r = requests.get(f"{API_BASE}/{doa_id}", timeout=15)
    r.raise_for_status()
    raw = r.json()

    # beberapa API mengembalikan 1 objek, atau {data: {...}}
    if isinstance(raw, dict) and ("data" in raw) and isinstance(raw["data"], dict):
        raw = raw["data"]

    # kalau masih berupa list, ambil elemen pertama
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        raw = raw[0]

    if debug:
        st.caption("Debug: respons mentah detail")
        st.json(raw)

    return _normalize_item(raw if isinstance(raw, dict) else {})

# ---------- UI utama ----------
def show_doa_harian():
    st.header("📖 Doa Harian (EQuran.id API)")

    # Kalau pengen debugging cepat:
    debug = st.toggle("Debug API response", value=False)

    # ambil daftar (tanpa filter dulu, filter manual di UI)
    data = fetch_list(debug=debug)

    if not data:
        st.warning("Tidak ada data dari API. Coba muat ulang atau periksa koneksi.")
        return

    # kumpulkan grup unik
    grups = sorted({d["grup"] for d in data})
    grup = st.selectbox("Kategori", grups, index=0)

    # filter sesuai grup
    opsi = [d for d in data if d["grup"] == grup]
    judul_map = {f"{d['judul']} #{d['id']}" if d['id'] else d['judul']: d["id"] for d in opsi}

    selected = st.selectbox("Pilih doa", list(judul_map.keys()))
    doa_id = judul_map.get(selected)

    # ambil detail by id agar konten lengkap/akurat
    det = fetch_detail(doa_id, debug=debug) if doa_id else {}

    st.subheader(det.get("judul", "Tanpa judul"))

    st.markdown("**Arab:**")
    st.write(det.get("arab", "") or "—")

    st.markdown("**Latin:**")
    st.write(det.get("latin", "") or "—")

    st.info(f"**Arti:** {det.get('indo', '-')}")
    st.caption("Sumber: EQuran.id")

    # tombol Copy
    _copy_button(f"{det.get('arab','')}\n\n{det.get('latin','')}\n\n{det.get('indo','-')}")

from streamlit.components.v1 import html
def _copy_button(text_to_copy: str):
    code = f"""
    <style>
      .copy-btn {{
        display:inline-block;padding:8px 14px;margin-top:10px;border-radius:6px;
        background:#10b981;color:white;font-weight:600;border:none;cursor:pointer
      }}
      .copy-btn:hover {{ filter:brightness(0.95) }}
    </style>
    <button class="copy-btn" onclick="
      navigator.clipboard.writeText(`{text_to_copy.replace('`','\\`')}`);
      var t=document.createElement('div');
      t.innerText='✅ Disalin'; t.style.position='fixed'; t.style.bottom='20px';
      t.style.right='20px'; t.style.background='#333'; t.style.color='#fff';
      t.style.padding='8px 12px'; t.style.borderRadius='6px'; t.style.zIndex='9999';
      document.body.appendChild(t); setTimeout(()=>t.remove(),1500);
    ">📋 Copy Doa</button>
    """
    html(code, height=60)
