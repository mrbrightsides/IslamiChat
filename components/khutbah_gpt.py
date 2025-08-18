import io
import textwrap
from datetime import date
import streamlit as st

def render_khutbah_form():
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

    if submitted:
        # placeholder untuk generate khutbah
        st.success("📜 Sedang membuat khutbah...")
        st.info(f"Jenis khutbah: {jenis_khutbah}")
        st.write(f"Tema: {tema or '(otomatis oleh AI)'}")
        st.write("➡️ Khutbah akan digenerate di bawah ini...")
        # panggil fungsi generate_khutbah() nanti

# ====== BANK DALIL SINGKAT (ringkas, aman untuk khutbah) ======
QURAN = {
    "taqwa": [
        ("Ali 'Imran 102", "Wahai orang-orang yang beriman! Bertakwalah kepada Allah sebenar-benar takwa kepada-Nya…"),
        ("Al-Hasyr 18", "Wahai orang-orang yang beriman! Bertakwalah kepada Allah, dan hendaklah setiap orang memperhatikan apa yang telah diperbuatnya untuk hari esok…"),
        ("An-Nahl 97", "Siapa beramal saleh—laki atau perempuan—dalam keadaan beriman, pasti Kami berikan kehidupan yang baik…"),
    ],
    "amanah": [
        ("An-Nisa 58", "Sungguh, Allah menyuruhmu menyampaikan amanat kepada yang berhak menerimanya…"),
        ("Al-Ahzab 72", "Sesungguhnya Kami telah menawarkan amanah kepada langit, bumi dan gunung-gunung…"),
    ],
    "ukhuwah": [
        ("Al-Hujurat 10", "Sesungguhnya orang-orang mukmin itu bersaudara…"),
        ("Al-Hujurat 13", "Wahai manusia! Sungguh Kami menciptakan kamu dari seorang laki-laki dan seorang perempuan…"),
    ],
    "ramadhan_idulfitri": [
        ("Al-Baqarah 183", "Wahai orang-orang yang beriman, diwajibkan atas kamu berpuasa…"),
        ("Al-Baqarah 185", "…agar kamu menyempurnakan bilangan (puasa) dan mengagungkan Allah…"),
    ],
    "iduladha": [
        ("As-Saffat 102-107", "Kisah pengorbanan Nabi Ibrahim dan Ismail ‘alaihimassalam…"),
        ("Al-Hajj 37", "Daging dan darah (hewan kurban) itu sekali-kali tidak sampai kepada Allah, tetapi ketakwaanmulah yang sampai kepada-Nya…"),
    ],
    "istisqa": [
        ("Nuh 10-12", "Mohonlah ampun kepada Tuhanmu, sungguh Dia Maha Pengampun. Niscaya Dia kirimkan hujan lebat atasmu…"),
        ("Hud 52", "Mohonlah ampun kepada Tuhanmu lalu bertaubatlah kepada-Nya, niscaya Dia menurunkan hujan lebat kepadamu…"),
    ],
    "nikah": [
        ("Ar-Rum 21", "Di antara tanda-tanda (kebesaran)-Nya, Dia menciptakan untukmu pasangan-pasangan… agar kamu cenderung dan merasa tenteram kepadanya…"),
        ("An-Nisa 1", "…bertakwalah kepada Allah yang dengan (mempergunakan) nama-Nya kamu saling meminta dan peliharalah hubungan silaturahim…"),
    ],
}

HADITH = {
    "taqwa": [
        ("Tirmidzi", "Bertakwalah kepada Allah di mana saja engkau berada; susullah keburukan dengan kebaikan yang akan menghapuskannya; dan pergaulilah manusia dengan akhlak yang baik."),
    ],
    "amanah": [
        ("Bukhari Muslim", "Tanda munafik itu tiga: apabila berbicara ia berdusta, apabila berjanji ia mengingkari, dan apabila dipercaya ia berkhianat."),
    ],
    "ukhuwah": [
        ("Muslim", "Janganlah kalian saling hasad, saling membenci, dan saling memutuskan; jadilah hamba-hamba Allah yang bersaudara."),
    ],
    "idulfitri": [
        ("Bukhari", "Barang siapa berpuasa Ramadan karena iman dan mengharap pahala, diampuni dosa-dosanya yang telah lalu."),
    ],
    "iduladha": [
        ("Ahmad", "Sebaik-baik amal pada hari-hari tasyriq adalah mengingat Allah dan menyembelih (kurban)."),
    ],
    "istisqa": [
        ("Abu Dawud", "Sesungguhnya beristighfar dapat menurunkan hujan."),
    ],
    "nikah": [
        ("Tirmidzi", "Sebaik-baik kalian adalah yang paling baik terhadap keluarganya…"),
    ],
}

def _pick(pack, n=1):
    out = []
    for i, item in enumerate(pack):
        if i >= n: break
        out.append(item)
    return out

def _wrap(p):
    return textwrap.fill(p, width=92)

def _bullets(points):
    return "\n".join([f"- {p}" for p in points])

def _make_opening(jenis):
    opener = (
        "Alhamdulillāh, segala puji bagi Allah Rabb semesta alam. "
        "Kita memuji-Nya, memohon pertolongan dan ampunan-Nya. "
        "Ashhadu an lā ilāha illallāh, wa ashhadu anna Muḥammadan ‘abduhū wa rasūluh. "
        "Allāhumma ṣalli ‘alā Muḥammad wa ‘alā ālihi wa ṣaḥbih."
    )
    wasiat = "Ma‘āsyiral muslimīn—marilah kita bertakwa kepada Allah dengan sebenar-benar takwa."
    if jenis == "Jumat":
        return _wrap(opener + " " + wasiat)
    return _wrap(opener + " " + wasiat)

def _make_closing(jenis):
    doa1 = (
        "Allāhumma ighfir lil-muslimīna wal-muslimāt, wal-mu’minīna wal-mu’mināt, "
        "al-aḥyā’i minhum wal-amwāt. Allāhumma inna nas’aluka hudā, wa tuqā, "
        "wal ‘afāfa wal ghina."
    )
    doa2 = "Rabbana ātinā fid-dunyā ḥasanah wa fil-ākhirati ḥasanah wa qinā ‘adzāban-nār."
    if jenis == "Jumat":
        return _wrap(doa1) + "\n\n" + _wrap(doa2) + "\n\n" + _wrap("Aqulu qawli hādzā, fastaghfirullāh li walakum.")
    else:
        return _wrap(doa1) + "\n\n" + _wrap(doa2)

def _default_theme_for(jenis):
    return {
        "Jumat": "Taqwa & Amanah",
        "Idul Fitri": "Syukur, Taqwa, dan Silaturahim",
        "Idul Adha": "Keteladanan Ibrahim & Makna Kurban",
        "Istisqa": "Taubat, Istighfar, dan Doa Meminta Hujan",
        "Nikah": "Mawaddah wa Rahmah dalam Rumah Tangga",
        "Umum": "Akhlak Mulia & Tanggung Jawab"
    }.get(jenis, "Taqwa")

def _theme_keys(jenis, tema):
    tema_l = (tema or _default_theme_for(jenis)).lower()
    keys = ["taqwa"]
    if any(k in tema_l for k in ["amanah","jujur","integritas"]): keys += ["amanah"]
    if any(k in tema_l for k in ["ukhuwah","persaudaraan","silatur"]): keys += ["ukhuwah"]
    if "fitri" in tema_l: keys += ["ramadhan_idulfitri"]
    if any(k in tema_l for k in ["adha","kurban","qurban","ibrahim"]): keys += ["iduladha"]
    if any(k in tema_l for k in ["hujan","istisqa","kemarau"]): keys += ["istisqa"]
    if any(k in tema_l for k in ["nikah","keluarga","rumah tangga"]): keys += ["nikah"]
    return list(dict.fromkeys(keys))  # unik, urutan terjaga

def _style_hint(gaya):
    return {
        "Formal": "",
        "Lugas": "Gunakan kalimat singkat dan langsung pada intinya.",
        "Puitis": "Sisipi majas seperlunya, jaga ritme dan rima ringan.",
        "Reflektif": "Ajak jamaah merenung dengan pertanyaan retoris.",
        "Ringan untuk Remaja": "Pakai contoh dekat keseharian: sekolah, gadget, media sosial."
    }.get(gaya, "")

def generate_khutbah(jenis, tema, gaya, panjang, audience, tanggal, tambahan):
    keys = _theme_keys(jenis, tema)
    # ambil 1–2 ayat & 1 hadith sesuai tema
    ayat = []
    for k in keys:
        ayat += _pick(QURAN.get(k, []), n=1)
    hadis = []
    base_hkey = {
        "Jumat": "taqwa",
        "Idul Fitri": "idulfitri",
        "Idul Adha": "iduladha",
        "Istisqa": "istisqa",
        "Nikah": "nikah",
        "Umum": "taqwa",
    }[jenis]
    hadis += _pick(HADITH.get(base_hkey, []), n=1)

    # outline butir pembahasan (disesuaikan panjang)
    target = max(300, min(1500, int(panjang)))
    n_points = 4 if target < 600 else (6 if target < 1000 else 8)
    points = [
        f"Menguatkan **takwa** sebagai poros amal dan solusi masalah umat.",
        f"Memahami makna **{_default_theme_for(jenis)}** dalam kehidupan sehari-hari.",
        "Contoh praktis dan langkah kecil yang bisa dimulai pekan ini.",
        "Menjaga lisan, amanah, dan etika bermedia.",
        "Peran keluarga/komunitas sebagai ekosistem kebajikan.",
        "Menutup dengan doa, mohon ampun dan kekuatan untuk istiqamah."
    ][:n_points]

    # bagian pembuka
    parts = []
    parts.append(_make_opening(jenis))

    # judul & metadata
    judul = tema or _default_theme_for(jenis)
    meta = f"**Tema:** {judul}"
    if audience: meta += f" • **Target:** {audience}"
    meta += f" • **Tanggal:** {tanggal.strftime('%d %B %Y')}"
    if (hint := _style_hint(gaya)):
        meta += f" • _Gaya_: {hint}"
    parts.append(meta)

    # sisipkan ayat & hadith
    if ayat:
        ay_lines = [f"> {n}: {t}" for (n, t) in ayat]
        parts.append("**Dalil Al-Qur’an:**\n" + "\n".join(ay_lines))
    if hadis:
        hd_lines = [f"> {src}: {t}" for (src, t) in hadis]
        parts.append("**Hadis:**\n" + "\n".join(hd_lines))

    # tubuh khutbah (ringkas tapi padat)
    paragraf = [
        f"Jamaah yang dimuliakan Allah, {judul} bukan sekadar jargon. Ia menuntut keyakinan yang benar, niat yang tulus, dan langkah nyata di rumah, di tempat kerja, dan di ruang digital.",
        "Kita mulai dari hal yang paling dekat: memperbaiki salat, menjaga amanah, menahan lisan, dan menunaikan hak sesama.",
        "Ketika individu-individu memperbaiki diri, Allah bukakan jalan kebaikan kolektif. Inilah sunnatullah: _InnaLlaha la yughayyiru ma biqawmin ḥattā yughayyirū mā bi-anfusihim_."
    ]
    parts.append("\n\n".join(map(_wrap, paragraf)))

    # bullet aksi
    parts.append("**Langkah praktis pekan ini:**\n" + _bullets(points))

    # tambahan pengguna
    if tambahan:
        parts.append("**Catatan khusus:** " + tambahan.strip())

    # penutup (doa)
    parts.append(_make_closing(jenis))

    # khusus Jumat: tambahkan Khutbah Kedua (sangat ringkas)
    if jenis == "Jumat":
        parts.append("---\n### Khutbah Kedua (ringkas)\n" +
                     _wrap("Alhamdulillāh, shalawat dan salam untuk Rasulullah. "
                           "Marilah memperbanyak istighfar dan shalawat. "
                           "Semoga Allah menjaga negeri ini, memudahkan rezeki yang halal, "
                           "serta menguatkan persatuan kaum Muslimin."))
        parts.append(_wrap("Allāhumma sholli ‘alā Muḥammad wa ‘alā āli Muḥammad… "
                           "Rabbana taqabbal minnā, innaka Antas-Samī‘ul ‘Alīm."))

    text = "\n\n".join(parts)

    # jaga target panjang kira-kira (tanpa over-engineering)
    # biarkan slider jadi _indikasi_ level detail, bukan angka presisi
    return text


# ====== UI ======
def render_khutbah_form():
    st.title("🕌 KhutbahGPT - Generator Khutbah Otomatis")
    st.markdown("Masukkan informasi di bawah ini untuk membuat teks khutbah:")

    with st.form("khutbah_form"):
        tanggal = st.date_input("Tanggal Khutbah", value=date.today())
        jenis_khutbah = st.radio(
            "Jenis Khutbah",
            ["Jumat", "Idul Fitri", "Idul Adha", "Istisqa", "Nikah", "Umum"],
            index=0
        )
        tema = st.text_input("Tema Khutbah (opsional)", placeholder="Contoh: Pentingnya Menjaga Amanah")
        gaya = st.selectbox("Gaya Bahasa", ["Formal", "Lugas", "Puitis", "Reflektif", "Ringan untuk Remaja"], index=0)
        panjang = st.slider("Panjang Khutbah (kata, indikatif)", 300, 1500, 700, 100)
        audience = st.text_input("Target Jamaah (opsional)", placeholder="Contoh: Mahasiswa, Jamaah Remaja, Umum")
        tambahan = st.text_area("Catatan atau Permintaan Khusus (opsional)", placeholder="Misal: Sertakan QS Al-‘Asr di pengantar")

        submitted = st.form_submit_button("🎙️ Buat Khutbah Sekarang")

    if not submitted:
        st.caption("👉 Setelah klik **Buat Khutbah Sekarang**, teks khutbah akan muncul di bawah.")
        return

    # generate
    text = generate_khutbah(jenis_khutbah, tema, gaya, panjang, audience, tanggal, tambahan)

    st.success("📜 Khutbah berhasil dibuat.")
    st.markdown(f"### {tema or _default_theme_for(jenis_khutbah)}")
    st.write(text)

    # download .txt
    buf = io.BytesIO(text.encode("utf-8"))
    st.download_button("💾 Unduh Teks (.txt)", data=buf.getvalue(),
                       file_name=f"Khutbah_{jenis_khutbah}_{tanggal.isoformat()}.txt",
                       mime="text/plain")
