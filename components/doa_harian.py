import requests
import streamlit as st
from streamlit.components.v1 import html

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60  # 1 jam

# ---------- utilities ----------
def _esc(s: str) -> str:
    return (s or "").replace("\\", "\\\\").replace("`", "\\`")

def copy_button(text_to_copy: str, label: str = "📋 Copy Doa"):
    html(
        f"""
        <style>
        .copy-btn{{
          display:inline-block;padding:8px 14px;margin-top:10px;border-radius:6px;
          background:#4CAF50;color:#fff;font-weight:600;border:none;cursor:pointer
        }}
        .copy-btn:hover{{background:#3f9b46}}
        </style>
        <button class="copy-btn" onclick="
          navigator.clipboard.writeText(`{_esc(text_to_copy or '')}`);
          const t=document.createElement('div');t.textContent='✅ Doa disalin';
          Object.assign(t.style,{{position:'fixed',bottom:'18px',right:'18px',
          background:'#333',color:'#fff',padding:'10px 14px',borderRadius:'6px',
          fontSize:'14px',zIndex:9999}});document.body.appendChild(t);
          setTimeout(()=>t.remove(),1800);
        ">{label}</button>
        """,
        height=0,
    )

def _first(*keys, src=None, default=""):
    for k in keys:
        v = (src or {}).get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return default

# ---------- API calls ----------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_list(grup: str | None = None, tag: str | None = None):
    params = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    # Normalisasi bentuk
    if isinstance(raw, dict):
        # kalau ada wrapper, ambil isinya
        raw = raw.get("data") or raw.get("result") or []

    if not isinstance(raw, list):
        return []

    out = []
    for x in raw:
        if not isinstance(x, dict):
            continue  # skip kalau bukan dict
        out.append({
            "id": x.get("id"),
            "grup": _first("grup", src=x, default="Tanpa Grup"),
            "judul": _first("doa", "judul", src=x, default=f"Tanpa judul #{x.get('id')}"),
            "arab":  _first("arab", "ayat", src=x, default=""),
            "latin": _first("latin", src=x, default=""),
            "indo":  _first("indo", "artinya", "terjemahan", "id", src=x, default=""),
        })
    return out

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_detail(doa_id: int):
    r = requests.get(f"{API_BASE}/{doa_id}", timeout=15)
    r.raise_for_status()
    x = r.json() or {}
    return {
        "id": x.get("id"),
        "grup": _first("grup", src=x, default="Tanpa Grup"),
        "judul": _first("doa", "judul", src=x, default=f"Tanpa judul #{x.get('id')}"),
        "arab":  _first("arab", "ayat", src=x, default=""),
        "latin": _first("latin", src=x, default=""),
        "indo":  _first("indo", "artinya", "terjemahan", "id", src=x, default=""),
    }

# ---------- UI ----------
def show_doa_harian():
    st.title("📖 Doa Harian (EQuran.id API)")

    # ambil semua & tampilkan kategori
    data = fetch_list()
    if not data:
        st.warning("Tidak ada data doa dari API.")
        return

    grups = sorted({ d.get("grup") or "Tanpa Grup" for d in data })
    grup  = st.selectbox("Kategori", grups)

    items = [d for d in data if (d.get("grup") or "Tanpa Grup") == grup]
    if not items:
        st.info("Tidak ada doa pada kategori ini.")
        return

    titles = [d["judul"] for d in items]
    picked = st.selectbox("Pilih doa", titles)
    base = next(d for d in items if d["judul"] == picked)

    # kalau konten kosong, fallback panggil detail /api/doa/{id}
    doa = base
    if not (base.get("arab") or base.get("latin") or base.get("indo")):
        try:
            doa = fetch_detail(int(base["id"]))
        except Exception:
            pass  # kalau gagal, tetap pakai base

    title = doa.get("judul") or f"Tanpa judul #{doa.get('id')}"
    arab  = doa.get("arab") or "-"
    latin = doa.get("latin") or "-"
    indo  = doa.get("indo") or "-"

    st.subheader(title)
    st.markdown(f"**Arab:**\n\n{arab}")
    st.markdown(f"**Latin:**\n\n{latin}")
    st.info(f"**Arti:** {indo}")
    st.caption("Sumber: EQuran.id")

    copy_button("\n\n".join([arab, latin, indo]))
