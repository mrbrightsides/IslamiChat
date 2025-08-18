# components/tab_hafalan_audio.py
import io, time, uuid
import streamlit as st
from urllib.parse import quote_plus
from tools_mushaf import MUSHAF

# ======================
# Helper
# ======================
def wa_prefill_link(phone_or_link: str, message: str) -> str:
    """phone_or_link bisa '62xxxx' atau link 'https://wa.me/62xxxx'."""
    raw = (phone_or_link or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        base = raw
    else:
        digits = "".join(ch for ch in raw if ch.isdigit())
        base = f"https://wa.me/{digits}" if digits else ""
    if not base:
        return ""
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}text={quote_plus(message)}"

def _audio_file_meta(upload) -> tuple[str, bytes]:
    """Return (filename, bytes) from Streamlit UploadedFile."""
    # buat nama unik untuk download lokal
    suffix = upload.name.split(".")[-1].lower() if "." in upload.name else "wav"
    fname = f"setor_{int(time.time())}_{uuid.uuid4().hex[:6]}.{suffix}"
    data = upload.read()
    return fname, data

# ======================
# (Optional) STT Stub
# ======================
def run_stt_stub(audio_bytes: bytes) -> str:
    """Stub: ganti dengan panggilan Whisper/Google jika siap.
    Sekarang hanya mengembalikan string kosong + catatan simulasi.
    """
    time.sleep(0.5)
    return ""  # kosong -> belum analisa beneran

# ======================
# UI
# ======================
def show_hafalan_audio_tab():
    st.title("🎙️ Setor Hafalan — Audio")
    st.caption(
        "Fitur ini adalah **simulasi pembelajaran** untuk membantu menyetor bacaan. "
        "Bukan penilaian tajwid resmi, dan **bukan fatwa**. "
        "Selalu rujuk dan konfirmasi kepada ustadz pembimbing."
    )

    # Pilih surah & rentang
    surah_key = st.selectbox(
        "Pilih Surah:",
        list(MUSHAF.keys()),
        format_func=lambda x: f"{x} — {MUSHAF[x]['name']}"
    )
    ayahs = MUSHAF[surah_key]["ayahs"]
    start, end = st.select_slider(
        "Pilih range ayat:",
        options=list(ayahs.keys()),
        value=(list(ayahs.keys())[0], list(ayahs.keys())[-1])
    )

    st.markdown("#### 📖 Teks Ayat (untuk dibaca saat setoran)")
    with st.container(border=True):
        for i in range(int(start), int(end) + 1):
            st.markdown(f"**Ayat {i}** — {ayahs[str(i)]}")

    st.divider()

    # Upload rekaman (audio-only alur)
    st.markdown("#### 🎧 Unggah Rekaman Bacaan")
    audio = st.file_uploader("Pilih file audio (mp3/wav/m4a/webm)", type=["mp3","wav","m4a","webm"])

    if "setor_audio_bytes" not in st.session_state:
        st.session_state.setor_audio_bytes = None
        st.session_state.setor_audio_name = None

    if audio is not None:
        fname, data = _audio_file_meta(audio)
        st.session_state.setor_audio_bytes = data
        st.session_state.setor_audio_name = fname

    if st.session_state.setor_audio_bytes:
        st.audio(st.session_state.setor_audio_bytes, format="audio/*")
        st.success("Rekaman siap. Kamu bisa simpan, kirim WA, atau hapus rekaman.")

        # ========== Aksi: Simpan / Kirim WA / Hapus ==========
        colA, colB, colC = st.columns([1,1,1])
        with colA:
            st.download_button(
                "⬇️ Simpan rekaman",
                data=st.session_state.setor_audio_bytes,
                file_name=st.session_state.setor_audio_name,
                mime="audio/*",
                use_container_width=True
            )
        with colB:
            # Prefill pesan: ringkasan surah & range
            summary = (
                f"Assalamu'alaikum Ustadz, saya setor hafalan:\n"
                f"- Surah: {MUSHAF[surah_key]['name']} ({surah_key})\n"
                f"- Ayat: {start}–{end}\n"
                f"(Audio terlampir)"
            )
            # Ganti nomor/link WA ustadz kalau mau langsung ke ustadz tertentu
            wa_link = wa_prefill_link("", summary)  # isi "" -> user pilih kontak WA sendiri
            st.link_button("💬 Kirim ke WhatsApp", wa_link if wa_link else "#", use_container_width=True)

        with colC:
            if st.button("❌ Hapus rekaman", type="secondary", use_container_width=True):
                st.session_state.setor_audio_bytes = None
                st.session_state.setor_audio_name = None
                st.toast("Rekaman dihapus dari sesi ini.", icon="🗑️")
                st.experimental_rerun()

        st.divider()

        # ========== Analisa (Opsional / Simulasi) ==========
        with st.expander("🧪 Analisa Otomatis (Opsional / Simulasi)", expanded=False):
            st.caption(
                "Analisa ini bersifat percobaan dan mungkin **tidak akurat**. "
                "Gunakan hanya sebagai bantuan belajar, bukan penilaian tajwid."
            )
            if st.button("▶️ Jalankan Analisa Simulasi"):
                trans = run_stt_stub(st.session_state.setor_audio_bytes)
                if not trans:
                    st.info(
                        "Belum terhubung ke layanan STT. "
                        "Nanti kita sambungkan ke Whisper/Google STT supaya transkrip otomatis muncul."
                    )
                else:
                    st.write("Transkrip:", trans)
    else:
        st.info("Unggah rekaman bacaanmu untuk mulai setoran.")
