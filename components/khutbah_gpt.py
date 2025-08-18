import streamlit as st
from datetime import date

def render_khutbah_form():
    st.title("🕌 KhutbahGPT - Generator Khutbah Otomatis")

    st.markdown("Masukkan informasi di bawah ini untuk membuat teks khutbah yang sesuai:")

    with st.form("khutbah_form"):
        tanggal = st.date_input("Tanggal Khutbah", value=date.today())
        jenis_khutbah = st.radio("Jenis Khutbah", ["Jumat", "Idul Fitri", "Idul Adha", "Istisqa", "Nikah", "Umum"], index=0)
        
        tema = st.text_input("Tema Khutbah (opsional)", placeholder="Contoh: Pentingnya Menjaga Amanah")
        gaya = st.selectbox("Gaya Bahasa", ["Formal", Lugas", "Puitis", "Reflektif", "Ringan untuk Remaja"])
        panjang = st.slider("Panjang Khutbah (kata)", min_value=300, max_value=1500, value=700, step=100)
        
        audience = st.text_input("Target Jamaah (opsional)", placeholder="Contoh: Mahasiswa, Jamaah Remaja, Umum")
        tambahan = st.text_area("Catatan atau Permintaan Khusus (opsional)", placeholder="Misal: Sertakan kutipan dari QS Al-Ashr")

        submitted = st.form_submit_button("🎙️ Buat Khutbah Sekarang")

    if submitted:
        # placeholder untuk generate khutbah
        st.success("📜 Sedang membuat khutbah...")
        st.info(f"Jenis khutbah: {jenis_khutbah}")
        st.write(f"Tema: {tema or '(otomatis oleh AI)'}")
        st.write("➡️ Khutbah akan digenerate di bawah ini...")
        # panggil fungsi generate_khutbah() nanti
