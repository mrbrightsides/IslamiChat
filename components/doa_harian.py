import requests
import streamlit as st
import base64, uuid
from typing import Any, Dict, List, Optional
from streamlit.components.v1 import html

API_BASE  = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60  # 1 jam

# =========================
# Helpers & Normalizers
# =========================
def _getv(d: Dict[str, Any], *candidates: str, default: str = "") -> str:
    """Ambil d[k] dengan beberapa fallback nama kunci."""
    for k in candidates:
        if k in d and d[k] is not None:
            return str(d[k])
    return default

def _normalize_container(raw: Any) -> List[Dict[str, Any]]:
    """Jika respons dibungkus 'data'/'result', ambil isinya; jika list, langsung pakai."""
    if isinstance(raw, dict):
        raw = raw.get("data") or raw.get("result") or raw.get("items") or []
    return raw if isinstance(raw, list) else []

def _normalize_item(x: Dict[str, Any]) -> Dict[str, Any]:
    """Samakan nama kunci dari berbagai kemungkinan API (EQuran.id paling utama)."""
    _id   = _getv(x, "id", "ID", "no", default="")
    judul = _getv(x, "nama", "doa", "title", "judul", default="") or (f"Tanpa judul #{_id}" if _id else "Tanpa judul")
    arab  = _getv(x, "ar", "ayat", "arab", "arabic", "arab_text")
    latin = _getv(x, "tr", "latin", "transliterasi", "latin_text")
    # JANGAN ambil 'id' di sini (bisa bentrok dengan numeric id)
    indo  = _getv(x, "idn", "artinya", "indo", "translation", "terjemahan")
    grup  = _getv(x, "grup", "group", "kategori", default="Tanpa Grup")
    ref   = _getv(x, "tentang", "sumber", "reference", "ket", default="")
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

# =========================
# Fetchers (cached)
# =========================
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_list(grup: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    items = _normalize_container(raw)
    return [_normalize_item(it) for it in items if isinstance(it, dict)]

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_detail(doa_id: str) -> Dict[str, Any]:
    if not doa_id:
        return {}
    r = requests.get(f"{API_BASE}/{doa_id}", timeout=15)
    r.raise_for_status()
    raw = r.json()

    # normalisasi bungkus
    if isinstance(raw, dict) and isinstance(raw.get("data"), dict):
        raw = raw["data"]
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        raw = raw[0]

    return _normalize_item(raw if isinstance(raw, dict) else {})

# =========================
# UI
# =========================
def show_doa_harian():
    st.header("📖 Doa Harian (EQuran.id API)")

    # Ambil daftar (tanpa filter)
    data = fetch_list()
    if not data:
        st.warning("Tidak ada data dari API. Coba muat ulang atau periksa koneksi.")
        return

    # Kategori unik
    grups = sorted({d["grup"] or "Tanpa Grup" for d in data})
    grup = st.selectbox("Kategori", grups, index=0 if grups else None)

    # Filter sesuai kategori
    opsi = [d for d in data if (d["grup"] or "Tanpa Grup") == grup] if grup else data

    # Label pilihan: judul + #id kalau ada
    judul_map = {
        (f"{d['judul']} #{d['id']}" if d['id'] else d['judul']): d["id"]
        for d in opsi
    }

    # Pilih doa
    selected_label = st.selectbox("Pilih doa", list(judul_map.keys()))
    doa_id = str(judul_map.get(selected_label, "")).strip()

    # Ambil detail by id (konten paling akurat)
    det = fetch_detail(doa_id) if doa_id else {}

    title = det.get("judul") or (f"Tanpa judul #{doa_id}" if doa_id else "Tanpa judul")
    st.subheader(title)

    st.markdown("**Arab:**")
    st.write(det.get("arab") or "—")

    st.markdown("**Latin:**")
    st.write(det.get("latin") or "—")

    st.markdown("**Arti:**")
    st.info(det.get("indo") or "—")

    # Keterangan/Hadits (opsional, dari 'tentang' EQuran)
    if det.get("ref"):
        with st.expander("Keterangan / Hadits", expanded=False):
            st.write(det["ref"])

    # Tag (opsional)
    tags = det.get("tags") or []
    if tags:
        st.caption("Tag: " + ", ".join(map(str, tags)))

    st.caption("Sumber: EQuran.id")

    # Tombol Copy (ikut sertakan keterangan jika ada)
    copy_text = "\n\n".join(
        [det.get("arab", ""), det.get("latin", ""), det.get("indo", "")]
        + ([det["ref"]] if det.get("ref") else [])
    ).strip()
    _copy_button(copy_text)

def _copy_button(text: str, label: str = "📋 Copy Doa"):
    """Tombol copy aman (escape-proof) pakai payload base64."""
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    btn_id = f"copy-{uuid.uuid4().hex}"

    html(f"""
<div id="{btn_id}">
  <button class="copy-btn">{label}</button>
</div>

<style>
  #{btn_id} .copy-btn {{
    display:inline-block; padding:8px 14px; border-radius:6px;
    background:#10b981; color:#fff; font-weight:600;
    border:none; cursor:pointer;
  }}
  #{btn_id} .copy-btn:hover {{ filter:brightness(0.95); }}
</style>

<script>
(function(){{
  const root = document.getElementById("{btn_id}");
  const btn  = root.querySelector(".copy-btn");
  const b64  = "{payload}";

  function utf8(atobStr){{
    try {{
      return decodeURIComponent(escape(atob(atobStr)));
    }} catch(e) {{
      return atob(atobStr);
    }}
  }}

  function showToast(){{
    const t = document.createElement('div');
    t.textContent = '✅ Disalin';
    Object.assign(t.style, {{
      position:'fixed', bottom:'20px', right:'20px',
      background:'#333', color:'#fff', padding:'8px 12px',
      borderRadius:'6px', zIndex: 9999, fontSize:'14px'
    }});
    document.body.appendChild(t);
    setTimeout(()=>t.remove(), 1500);
  }}

  function fallbackCopy(text){{
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position='fixed';
    ta.style.top='-1000px';
    document.body.appendChild(ta);
    ta.select();
    try {{ document.execCommand('copy'); showToast(); }}
    finally {{ ta.remove(); }}
  }}

  btn.addEventListener('click', () => {{
    const text = utf8(b64);
    if (navigator.clipboard && window.isSecureContext) {{
      navigator.clipboard.writeText(text).then(showToast).catch(() => fallbackCopy(text));
    }} else {{
      fallbackCopy(text);
    }}
  }});
}})();
</script>
""", height=80)
