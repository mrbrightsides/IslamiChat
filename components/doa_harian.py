import streamlit as st

DOA_LIST = {
    "Doa Pagi": {
        "arab": "اَللَّهُمَّ بِكَ أَصْبَحْنَا وَبِكَ أَمْسَيْنَا ...",
        "latin": "Allahumma bika ashbahna wa bika amsaina ...",
        "arti": "Ya Allah, dengan-Mu kami berada di pagi hari dan dengan-Mu kami berada di sore hari ..."
    },
    "Doa Sebelum Tidur": {
        "arab": "بِاسْمِكَ اللَّهُمَّ أَحْيَا وَبِاسْمِكَ أَمُوتُ",
        "latin": "Bismika Allahumma ahyaa wa bismika amuut",
        "arti": "Dengan nama-Mu ya Allah aku hidup dan dengan nama-Mu aku mati."
    },
    "Doa Keluar Rumah": {
        "arab": "بِسْمِ اللهِ تَوَكَّلْتُ عَلَى اللهِ ...",
        "latin": "Bismillah, tawakkaltu ‘alallaah ...",
        "arti": "Dengan nama Allah, aku bertawakal kepada Allah ..."
    }
}

def show_doa_harian():
    st.title("📖 Doa Harian (Hisnul Muslim)")
    st.caption("Kumpulan doa pendek sehari-hari, lengkap Arab, Latin, dan artinya.")

    pilihan = st.selectbox("Pilih doa", list(DOA_LIST.keys()))

    doa = DOA_LIST[pilihan]
    st.markdown(f"### {pilihan}")
    st.markdown(f"**Arab:**\n\n {doa['arab']}")
    st.markdown(f"**Latin:**\n\n {doa['latin']}")
    st.info(f"**Arti:** {doa['arti']}")

    # Tombol copy / share (opsional)
    if st.button("📋 Copy ke Clipboard"):
        st.toast("Teks doa sudah disalin ✅")

    # Tombol play audio (kalau ada file audio)
    if st.button("🔊 Play Audio"):
        st.audio("https://example.com/doa.mp3")  # ganti dengan URL audio asli
