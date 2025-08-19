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

    # copy teks doa (pakai text_area supaya bisa di-copy manual)
    st.text_area("📋 Salin teks doa:", f"{doa['arab']}\n\n{doa['latin']}\n\n{doa['translation_id']}", height=150)

    # share (opsional: buat URL Whatsapp)
    share_url = f"https://wa.me/?text={doa['title']}%0A{doa['arab']}%0A{doa['latin']}%0A{doa['translation_id']}"
    st.markdown(f"[🔗 Share via WhatsApp]({share_url})")
