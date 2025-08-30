import json, requests, streamlit as st
from pathlib import Path
from streamlit.components.v1 import html

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60 * 12  # 12 jam

# ----------------- Data loaders -----------------
def load_local():
    p = Path("data/doa_harian.json")
    return json.loads(p.read_text(encoding="utf-8"))

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_api(grup: str | None = None, tag: str | None = None):
    params = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    # Pastikan bentuknya list
    if isinstance(raw, dict):
        # Kalau respons ada key "data"
        if "data" in raw and isinstance(raw["data"], list):
            raw = raw["data"]
        else:
            raw = [raw]
    if not isinstance(raw, list):
        raise ValueError(f"Unexpected API response: {type(raw)}")

    norm = []
    for x in raw:
        if not isinstance(x, dict):
            continue
        norm.append({
            "id": x.get("id"),
            "title": x.get("doa") or x.get("judul") or "Tanpa judul",
            "arab": x.get("ayat") or x.get("arab") or "",
            "latin": x.get("latin") or x.get("transliterasi") or "",
            "translation_id": x.get("artinya") or x.get("arti") or "",
            "source": "EQuran.id",
            "category": (x.get("grup") or x.get("kategori") or "Lainnya").title(),
            "audio_url": x.get("audio") or None,
            "tags": x.get("tag") or x.get("tags") or [],
        })
    return norm

def load_hybrid(mode: str, grup: str | None, tag: str | None):
    """
    mode: 'Auto', 'API only', 'Local only'
    """
    if mode == "Local only":
        return load_local(), "local"
    if mode in ("Auto", "API only"):
        try:
            data = fetch_api(grup or None, tag or None)
            if not data:
                raise ValueError("API returned empty")
            return data, "api"
        except Exception as e:
            if mode == "API only":
                raise
            st.warning(f"API tidak tersedia, memakai data lokal. ({e})")
            return load_local(), "local"

# ----------------- UI helpers -----------------
def copy_button(text_to_copy: str):
    copy_code = f"""
    <style>
    .copy-btn {{display:inline-block;padding:8px 14px;margin-top:10px;border-radius:6px;
                background:#4CAF50;color:#fff;font-weight:600;cursor:pointer;border:none}}
    .copy-btn:hover {{background:#45a049}}
    </style>
    <button class="copy-btn" onclick="navigator.clipboard.writeText(`{text_to_copy}`);
      var t=document.createElement('div'); t.innerText='✅ Doa disalin!';
      t.style.position='fixed'; t.style.bottom='20px'; t.style.right='20px';
      t.style.background='#333'; t.style.color='#fff'; t.style.padding='10px 14px';
      t.style.borderRadius='6px'; t.style.fontSize='14px'; t.style.zIndex='9999';
      document.body.appendChild(t); setTimeout(()=>t.remove(),1600);">
      📋 Copy Doa
    </button>
    """
    html(copy_code, height=64)

# ----------------- Page -----------------
def show_doa_harian():
    st.title("📖 Doa Harian")

    with st.expander("Sumber & Filter", expanded=True):
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            mode = st.selectbox("Sumber data", ["Auto", "API only", "Local only"], index=0,
                                help="Auto: pakai API, kalau gagal fallback ke data lokal.")
        with c2:
            grup = st.text_input("Filter grup (opsional)",
                                 placeholder="Contoh: Doa Sebelum dan Sesudah Tidur")
        with c3:
            tag = st.text_input("Filter tag (opsional)", placeholder="Contoh: malam, safar, hujan")

    data, used = load_hybrid(mode, grup.strip() or None, tag.strip() or None)
    st.caption(f"Data source: **{'EQuran.id API' if used=='api' else 'Hisnul Muslim (offline)'}**"
               + (f" • grup: `{grup}`" if grup else "")
               + (f" • tag: `{tag}`" if tag else "")
               )

    # Kategori
    cats = sorted({(d.get("category") or 'Lainnya').title() for d in data}) or ["Lainnya"]
    cat = st.selectbox("Kategori", cats)

    items = [d for d in data if (d.get("category") or 'Lainnya').title() == cat]
    q = st.text_input("Cari (judul/arab/latin)", "")
    if q:
        ql = q.lower()
        items = [d for d in items if any(ql in (d.get(k,"").lower()) for k in ("title","arab","latin"))]

    if not items:
        st.info("Tidak ada doa pada filter ini.")
        return

    opt = st.selectbox("Pilih doa", [d["title"] for d in items])
    doa = next(d for d in items if d["title"] == opt)

    st.subheader(doa["title"])
    if doa.get("arab"):  st.markdown(f"**Arab:**\n\n{doa['arab']}")
    if doa.get("latin"): st.markdown(f"**Latin:**\n\n{doa['latin']}")
    if doa.get("translation_id"):
        st.info(f"**Arti:** {doa['translation_id']}")
    st.caption(f"Sumber: {doa.get('source','')}")

    if doa.get("audio_url"):
        st.audio(doa["audio_url"])

    copy_button("\n\n".join(filter(None, [
        doa.get("arab",""), doa.get("latin",""), doa.get("translation_id","")
    ])))

# panggil di app utama
if __name__ == "__main__":
    show_doa_harian()
