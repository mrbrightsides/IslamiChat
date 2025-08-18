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

# ===== Offline fallback: generator khutbah sederhana =====
import textwrap

def generate_khutbah(jenis, tema, gaya, panjang, audience, tanggal, tambahan):
    judul_default = {
        "Jumat": "Taqwa & Amanah",
        "Idul Fitri": "Syukur, Taqwa, dan Silaturahim",
        "Idul Adha": "Keteladanan Ibrahim & Makna Kurban",
        "Istisqa": "Taubat, Istighfar, dan Doa Meminta Hujan",
        "Nikah": "Mawaddah wa Rahmah dalam Rumah Tangga",
        "Umum": "Akhlak Mulia & Tanggung Jawab",
    }.get(jenis, "Taqwa")
    judul = (tema or judul_default).strip()

    hint = {
        "Formal": "",
        "Lugas": "Kalimat singkat dan langsung.",
        "Puitis": "Majas ringan; jaga ritme.",
        "Reflektif": "Pertanyaan retoris untuk merenung.",
        "Ringan untuk Remaja": "Contoh dekat: sekolah, gadget, media sosial.",
    }.get(gaya, "")

    def wrap(x): return textwrap.fill(x, 92)

    pembuka = wrap(
        "Alhamdulillāh, segala puji bagi Allah Rabb semesta alam. "
        "Kita memuji-Nya, memohon pertolongan dan ampunan-Nya. "
        "Ashhadu an lā ilāha illallāh, wa ashhadu anna Muḥammadan ‘abduhū wa rasūluh. "
        "Allāhumma ṣalli ‘alā Muḥammad wa ‘alā ālihi wa ṣaḥbih. "
        "Ma‘āsyiral muslimīn—marilah kita bertakwa kepada Allah dengan sebenar-benar takwa."
    )

    meta = f"**Tema:** {judul}"
    if audience: meta += f" • **Target:** {audience}"
    meta += f" • **Tanggal:** {tanggal.strftime('%d %B %Y')}"
    if hint: meta += f" • _Gaya_: {hint}"

    # jumlah poin sesuai slider panjang (indikatif)
    target = max(300, min(1500, int(panjang)))
    n_points = 4 if target < 600 else (6 if target < 1000 else 8)
    poin = [
        "Menguatkan ketakwaan sebagai poros amal.",
        f"Memaknai '{judul}' dalam keseharian: ibadah, keluarga, kerja, dan ruang digital.",
        "Menjaga amanah, lisan, dan etika bermedia.",
        "Memulai langkah kecil pekan ini dan saling menasihati dalam kebaikan.",
        "Merawat silaturahim dan kepedulian sosial.",
        "Berdoa, beristighfar, dan menghidupkan salat berjamaah.",
        "Membangun budaya belajar dan membaca Al-Qur’an di rumah.",
        "Menjauhi perkara syubhat dan kebiasaan sia-sia.",
    ][:n_points]

    badan = "\n\n".join(map(wrap, [
        f"Jamaah yang dimuliakan Allah, {judul} bukan sekadar slogan. Ia menuntut keyakinan yang benar, niat yang lurus, dan langkah nyata.",
        "Mari kita mulai dari yang paling dekat: memperbaiki salat, menunaikan amanah, menahan lisan, serta berbuat baik kepada sesama.",
        "Ketika pribadi-pribadi memperbaiki diri, Allah bukakan jalan kebaikan kolektif. Inilah sunnatullah yang tidak berubah."
    ]))

    bullets = "\n".join(f"- {p}" for p in poin)

    doa1 = wrap(
        "Allāhumma ighfir lil-muslimīna wal-muslimāt, wal-mu’minīna wal-mu’mināt, "
        "al-aḥyā’i minhum wal-amwāt. Allāhumma inna nas’aluka hudā, wa tuqā, "
        "wal ‘afāfa wal ghina."
    )
    doa2 = wrap("Rabbana ātinā fid-dunyā ḥasanah wa fil-ākhirati ḥasanah wa qinā ‘adzāban-nār.")
    penutup = doa1 + "\n\n" + doa2
    if jenis == "Jumat":
        penutup += "\n\n" + wrap("Aqulu qawli hādzā, fastaghfirullāh li walakum.")

    if tambahan:
        tambahan_txt = "\n\n" + "**Catatan khusus panitia/jamaah:** " + tambahan.strip()
    else:
        tambahan_txt = ""

    teks = (
        pembuka + "\n\n" +
        meta + "\n\n" +
        badan + "\n\n" +
        "**Langkah praktis pekan ini:**\n" + bullets +
        tambahan_txt + "\n\n" +
        penutup + (
            "\n\n---\n### Khutbah Kedua (ringkas)\n" +
            wrap("Alhamdulillāh, shalawat dan salam untuk Rasulullah. "
                 "Perbanyak istighfar dan shalawat; semoga Allah menjaga negeri ini, "
                 "memudahkan rezeki yang halal, serta menguatkan persatuan kaum Muslimin.")
            if jenis == "Jumat" else ""
        )
    )
    return teks

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
