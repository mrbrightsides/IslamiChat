import json, streamlit as st
from pathlib import Path

def load_doa():
    p = Path("data/doa_harian.json")
    return json.loads(p.read_text(encoding="utf-8"))

def show_doa_harian():
    data = load_doa()
    st.title("📖 Doa Harian (Hisnul Muslim)")

    # pilih kategori
    cats = sorted(set(item["category"] for item in data))
    cat = st.selectbox("Kategori", cats, index=0)

    # filter doa berdasarkan kategori
    items = [d for d in data if d["category"] == cat]
    opt = st.selectbox("Pilih doa", [d["title"] for d in items])
    doa = next(d for d in items if d["title"] == opt)

    # tampilkan konten doa
    st.subheader(doa["title"])
    st.markdown(f"**Arab:**\n\n{doa['arab']}")
    st.markdown(f"**Latin:**\n\n{doa['latin']}")
    st.info(f"**Arti:** {doa['translation_id']}")
    st.caption(f"Sumber: {doa['source']}")

    # audio opsional
    if doa.get("audio_url"):
        st.audio(doa["audio_url"])

    copy_button(f"{doa['arab']}\n\n{doa['latin']}\n\n{doa['translation_id']}")

import streamlit as st

def copy_button(text_to_copy: str):
    copy_code = f"""
    <style>
    .copy-btn {{
        display:inline-block;
        padding:8px 14px;
        margin-top:10px;
        border-radius:6px;
        background-color:#4CAF50;
        color:white;
        font-weight:bold;
        cursor:pointer;
        border:none;
        transition:0.2s;
    }}
    .copy-btn:hover {{
        background-color:#45a049;
    }}
    </style>

    <button class="copy-btn" onclick="navigator.clipboard.writeText(`{text_to_copy}`)">
        📋 Copy Doa
    </button>
    """
    st.markdown(copy_code, unsafe_allow_html=True)
