import requests, streamlit as st

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60 * 12  # 12 jam

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_api(grup: str | None = None, tag: str | None = None):
    params = {}
    if grup: params["grup"] = grup
    if tag: params["tag"] = tag
    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def show_doa_harian():
    st.title("📖 Doa Harian (EQuran.id API)")

    # ambil data langsung dari API
    data = fetch_api()

    if not data:
        st.warning("Tidak ada data doa ditemukan.")
        return

    # tampilkan kategori unik
    grups = sorted(set(x.get("grup", "Tanpa Grup") for x in data))
    grup = st.selectbox("Kategori", grups)

    # filter sesuai grup
    items = [d for d in data if d.get("grup") == grup]
    opt = st.selectbox("Pilih doa", [d.get("judul", f"Tanpa judul #{d.get('id')}") for d in items])
    doa = next(d for d in items if d.get("judul") == opt)

    # tampilkan detail
    st.subheader(doa.get("judul", "Tanpa judul"))
    st.markdown(f"**Arab:**\n\n{doa.get('arab','-')}")
    st.markdown(f"**Latin:**\n\n{doa.get('latin','-')}")
    st.info(f"**Arti:** {doa.get('indo','-')}")
    st.caption("Sumber: EQuran.id")

    # tombol copy
    copy_button(f"{doa.get('arab','')}\n\n{doa.get('latin','')}\n\n{doa.get('indo','')}")

from streamlit.components.v1 import html
def copy_button(text_to_copy: str):
    html(f"""
    <button onclick="navigator.clipboard.writeText(`{text_to_copy}`)" 
            style="padding:8px 14px; border:none; border-radius:6px;
                   background:#4CAF50; color:white; font-weight:bold;
                   cursor:pointer;">
        📋 Copy Doa
    </button>
    """, height=40)
