import requests, streamlit as st
# === Copy-to-Clipboard helper (Streamlit) ===
from streamlit.components.v1 import html

def _esc(s: str) -> str:
    # amankan backslash & backtick biar tidak pecah di template literal JS
    return (s or "").replace("\\", "\\\\").replace("`", "\\`")

def copy_button(text_to_copy: str, label: str = "📋 Copy Doa"):
    payload = _esc(text_to_copy or "")
    html(
        f"""
        <style>
        .copy-btn {{
            display:inline-block; padding:8px 14px; margin-top:10px;
            border-radius:6px; background:#4CAF50; color:#fff; font-weight:600;
            border:none; cursor:pointer; transition:.15s;
        }}
        .copy-btn:hover {{ background:#3f9b46; }}
        </style>
        <button class="copy-btn" onclick="
            navigator.clipboard.writeText(`{payload}`);
            const t=document.createElement('div');
            t.textContent='✅ Doa disalin';
            Object.assign(t.style, {{
                position:'fixed', bottom:'18px', right:'18px',
                background:'#333', color:'#fff', padding:'10px 14px',
                borderRadius:'6px', fontSize:'14px', zIndex:9999
            }});
            document.body.appendChild(t); setTimeout(()=>t.remove(),1800);
        ">{label}</button>
        """,
        height=0,
    )

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60 * 12  # 12 jam

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_api(grup: str | None = None, tag: str | None = None):
    params = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    # --- Normalisasi respons agar selalu list[dict] ---
    rows = raw
    if isinstance(raw, dict):
        # kalau API berbentuk {"data":[...]} atau mirip
        if "data" in raw and isinstance(raw["data"], list):
            rows = raw["data"]
        # kalau payloadnya salah satu kunci menyimpan list
        elif any(isinstance(v, list) for v in raw.values()):
            for v in raw.values():
                if isinstance(v, list):
                    rows = v
                    break

    if isinstance(rows, dict):
        rows = [rows]

    norm_rows: list[dict] = []
    for x in rows:
        if isinstance(x, dict):
            norm_rows.append(x)
        else:
            norm_rows.append({"judul": str(x), "arab": "", "latin": "", "indo": "", "grup": "Lainnya"})

    return norm_rows

def safe_get(d: dict, key: str, default=""):
    return d.get(key, default) if isinstance(d, dict) else default

def show_doa_harian():
    st.title("📖 Doa Harian (EQuran.id API)")

    data = fetch_api()              # sudah kita normalisasi sebelumnya
    if not data:
        st.warning("Tidak ada data doa ditemukan.")
        return

    # kategori/grup aman
    grups = sorted({ (d.get("grup") or "Tanpa Grup") for d in data })
    grup  = st.selectbox("Kategori", grups)

    items = [d for d in data if (d.get("grup") or "Tanpa Grup") == grup]
    if not items:
        st.info("Tidak ada doa pada kategori ini.")
        return

    titles = [d.get("judul") or d.get("doa") or f"Tanpa judul #{d.get('id')}" for d in items]
    picked = st.selectbox("Pilih doa", titles)

    doa = next(d for d in items if (d.get("judul") or d.get("doa") or f"Tanpa judul #{d.get('id')}") == picked)

    title = doa.get("judul") or doa.get("doa") or "Tanpa judul"
    arab  = (doa.get("arab")  or doa.get("ayat")   or "").strip()
    latin = (doa.get("latin") or "").strip()
    indo  = (doa.get("indo")  or doa.get("artinya") or "").strip()

    st.subheader(title)
    st.markdown(f"**Arab:**\n\n{arab or '-'}")
    st.markdown(f"**Latin:**\n\n{latin or '-'}")
    st.info(f"**Arti:** {indo or '-'}")
    st.caption("Sumber: EQuran.id")

    # tombol copy — sekarang sudah terdefinisi
    copy_button("\n\n".join([arab or "-", latin or "-", indo or "-"]))

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_doa_by_id(doa_id: int):
    r = requests.get(f"{API_BASE}/{doa_id}", timeout=15)
    r.raise_for_status()
    raw = r.json()
    if isinstance(raw, dict) and "data" in raw:
        raw = raw["data"]
    if not isinstance(raw, dict):
        return None
    return {
        "id":    raw.get("id"),
        "grup":  raw.get("grup", "Tanpa Grup"),
        "judul": raw.get("doa") or raw.get("judul", "Tanpa judul"),
        "arab":  raw.get("ayat") or raw.get("arab", ""),
        "latin": raw.get("latin", ""),
        "indo":  raw.get("artinya") or raw.get("indo", ""),
        "audio": raw.get("audio"),
    }
