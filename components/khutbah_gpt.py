import io
import textwrap
from datetime import date
import streamlit as st

# ====== Helper GPT (opsional) ======
import os
try:
    from openai import OpenAI
except Exception:
    OpenAI = None  # biar aman kalau lib belum terpasang

def _has_openai_key() -> bool:
    key = getattr(st, "secrets", {}).get("OPENAI_API_KEY", None) if hasattr(st, "secrets") else None
    key = key or os.getenv("OPENAI_API_KEY")
    return bool(key) and (OpenAI is not None)

def _build_prompt(jenis, tema, gaya, panjang, audience, tanggal, tambahan):
    judul = tema or {
        "Jumat":"Taqwa & Amanah",
        "Idul Fitri":"Syukur & Silaturahim",
        "Idul Adha":"Keteladanan Ibrahim & Makna Kurban",
        "Istisqa":"Taubat & Doa Meminta Hujan",
        "Nikah":"Mawaddah wa Rahmah",
        "Umum":"Akhlak & Tanggung Jawab",
    }.get(jenis,"Taqwa")

    hint = {
        "Formal": "",
        "Lugas": "Kalimat pendek dan langsung.",
        "Puitis": "Majas ringan; jaga ritme.",
        "Reflektif": "Pertanyaan retoris untuk ajak merenung.",
        "Ringan untuk Remaja": "Contoh dekat: sekolah, gadget, media sosial.",
    }.get(gaya,"")

    return f"""
TULIS KHUTBAH berbahasa Indonesia, sopan, sesuai adab mimbar.
Jenis: {jenis}
Tema: {judul}
Gaya: {gaya} {('('+hint+')') if hint else ''}
Target kata (indikatif): {int(panjang)}
Target jamaah: {audience or 'Umum'}
Tanggal: {tanggal.isoformat()}

Struktur:
- Pembukaan (hamdalah, shalawat, wasiat takwa)
- Ayat/hadits singkat (cukup terjemah & rujukan ringkas)
- 3–6 paragraf inti sesuai tema/jenis khutbah
- 3–6 poin aksi praktis
- Penutup (doa ma’tsur ringkas). Untuk Jumat, sertakan ringkasan khutbah kedua.

Kaidah:
- Hindari konten sensitif/politis; tekankan akhlak & ibadah.
- Rujukan Qur’an/Hadits singkat: (QS. Al-Hasyr:18), (HR. Muslim).
- Bahasa jelas dan mudah.
Tambahan: {tambahan or '-'}
""".strip()

def generate_khutbah_gpt(jenis, tema, gaya, panjang, audience, tanggal, tambahan, model="gpt-4o-mini") -> str:
    if not _has_openai_key():
        raise RuntimeError("OPENAI_API_KEY atau library openai belum tersedia.")
    api_key = st.secrets.get("OPENAI_API_KEY", None) if hasattr(st, "secrets") else None
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    system = ("You are KhutbahGPT, an imam assistant that writes concise, responsible khutbah texts "
              "in Indonesian. Keep it respectful, apolitical, and practical.")
    prompt = _build_prompt(jenis, tema, gaya, panjang, audience, tanggal, tambahan)

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":prompt}],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ====== UI: tampilan persis seperti punyamu, hasil Offline di bawah GPT ======
def render_khutbah_form():
    from datetime import date
    st.title("🕌 KhutbahGPT - Generator Khutbah Otomatis")
    st.markdown("Masukkan informasi di bawah ini untuk membuat teks khutbah yang sesuai:")

    with st.form("khutbah_form"):
        tanggal = st.date_input("Tanggal Khutbah", value=date.today())
        jenis_khutbah = st.radio("Jenis Khutbah", ["Jumat", "Idul Fitri", "Idul Adha", "Istisqa", "Nikah", "Umum"], index=0)
        tema = st.text_input("Tema Khutbah (opsional)", placeholder="Contoh: Pentingnya Menjaga Amanah")
        gaya = st.selectbox("Gaya Bahasa", ["Formal", "Lugas", "Puitis", "Reflektif", "Ringan untuk Remaja"])
        panjang = st.slider("Panjang Khutbah (kata)", min_value=300, max_value=1500, value=700, step=100)
        audience = st.text_input("Target Jamaah (opsional)", placeholder="Contoh: Mahasiswa, Jamaah Remaja, Umum")
        tambahan = st.text_area("Catatan atau Permintaan Khusus (opsional)", placeholder="Misal: Sertakan kutipan dari QS Al-Ashr")
        submitted = st.form_submit_button("🎙️ Buat Khutbah Sekarang")

    if not submitted:
        return

    st.success("📜 Sedang membuat khutbah...")
    st.info(f"Jenis khutbah: **{jenis_khutbah}** • Tema: **{tema or '(otomatis oleh AI)'}**")

    # === 1) Coba GPT dulu (jika tersedia), tampil sebagai hasil utama ===
    gpt_text = None
    gpt_error = None
    if _has_openai_key():
        with st.spinner("🧠 GPT sedang menyusun teks..."):
            try:
                gpt_text = generate_khutbah_gpt(jenis_khutbah, tema, gaya, panjang, audience, tanggal, tambahan)
            except Exception as e:
                gpt_error = str(e)

    if gpt_text:
        st.subheader("✳️ Hasil (GPT)")
        st.write(gpt_text)
        st.download_button(
            "💾 Unduh Teks GPT (.txt)",
            data=gpt_text.encode("utf-8"),
            file_name=f"Khutbah_{jenis_khutbah}_{tanggal.isoformat()}_GPT.txt",
            mime="text/plain",
            use_container_width=True
        )
    else:
        if gpt_error:
            st.warning(f"Gagal menggunakan GPT: {gpt_error}. Menampilkan versi Offline.")

    # === 2) Selalu tampilkan versi Offline di bawahnya ===
    # NOTE: pastikan kamu punya fungsi offline: generate_khutbah(...)
    offline_text = generate_khutbah(jenis_khutbah, tema, gaya, panjang, audience, tanggal, tambahan)
    st.subheader("🧩 Versi Template (Offline)")
    st.write(offline_text)
    st.download_button(
        "💾 Unduh Teks Offline (.txt)",
        data=offline_text.encode("utf-8"),
        file_name=f"Khutbah_{jenis_khutbah}_{tanggal.isoformat()}_Offline.txt",
        mime="text/plain",
        use_container_width=True
    )
