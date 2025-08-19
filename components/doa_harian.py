import json, streamlit as st
from pathlib import Path

def load_doa():
    p = Path("data/doa_harian.json")
    return json.loads(p.read_text(encoding="utf-8"))

def show_doa_harian():
    data = load_doa()
    st.title("📖 Doa Harian (Hisnul Muslim)")
    cats = sorted(set(item["category"] for item in data))
    cat = st.selectbox("Kategori", cats, index=0)
    items = [d for d in data if d["category"] == cat]
    opt = st.selectbox("Pilih doa", [f'{d["title"]}' for d in items])
    doa = next(d for d in items if d["title"] == opt)

    st.subheader(doa["title"])
    st.markdown(f"**Arab:**\n\n{doa['arab']}")
    st.markdown(f"**Latin:**\n\n{doa['latin']}")
    st.info(f"**Arti:** {doa['translation_id']}")
    if doa.get("audio_url"):
        st.audio(doa["audio_url"])

    # Tombol copy / share (opsional)
    if st.button("📋 Copy ke Clipboard"):
        st.toast("Teks doa sudah disalin ✅")

    # Tombol play audio (kalau ada file audio)
    if st.button("🔊 Play Audio"):
        st.audio("https://example.com/doa.mp3")  # ganti dengan URL audio asli
