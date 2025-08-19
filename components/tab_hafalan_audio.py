import io, time, uuid, os
import streamlit as st
from urllib.parse import quote_plus
from tools_mushaf import MUSHAF

# ======================
# KONFIGURASI
# ======================
# Isi nomor/link WA jika ingin langsung ke ustadz tertentu.
USTADZ_LIST = [
    {"name": "Dr. Heri Iskandar, M.Pd", "wa": "6289675674860"},
    {"name": "Sawi Sujarwo, M.Psi",     "wa": "62xxxxxxxxxx"},
]
# Pesan pembuka default ke WA:
WA_GREETING = "Assalamu'alaikum Ustadz, saya setor hafalan:"

# ======================
# Helper
# ======================
def wa_prefill_link(phone_or_link: str, message: str) -> str:
    """phone_or_link bisa '62xxxx' atau link 'https://wa.me/62xxxx'.
    kalau kosong => user pilih kontak WA sendiri.
    """
    raw = (phone_or_link or "").strip()
    if not raw:
        base = "https://wa.me/"
    elif raw.startswith(("http://", "https://")):
        base = raw
    else:
        digits = "".join(ch for ch in raw if ch.isdigit())
        base = f"https://wa.me/{digits}" if digits else "https://wa.me/"
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}text={quote_plus(message)}"

def _audio_file_meta(upload) -> tuple[str, bytes]:
    suffix = upload.name.split(".")[-1].lower() if "." in upload.name else "wav"
    fname = f"setor_{int(time.time())}_{uuid.uuid4().hex[:6]}.{suffix}"
    data = upload.read()
    return fname, data

# ======================
# STT (Opsional)
# ======================
def run_stt(audio_bytes: bytes) -> str:
    """
    Transkripsi audio -> teks Arab (jika memungkinkan).
    - Coba OpenAI Whisper via API jika OPENAI_API_KEY tersedia di st.secrets / env.
    - Jika tidak tersedia, kembalikan string kosong (analisa skip).
    """
    # Ambil API key dari st.secrets dulu, lalu environment vars sbg fallback
    api_key = st.secrets.get("OPENAI_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        return ""  # belum dikonfigurasi -> skip

    try:
        # OpenAI SDK v1
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Simpan sementara ke buffer file-like
        buf = io.BytesIO(audio_bytes)
        buf.name = "setoran_audio.webm"  # nama dummy; SDK butuh nama

        # whisper-1 biasanya mengembalikan bahasa asli;
        # kita set language='ar' agar cenderung mengembalikan aksara Arab.
        trans = client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
            language="ar"
        )
        text = getattr(trans, "text", "")
        return text or ""
    except Exception as e:
        # Tidak gagal keras: cukup kembalikan kosong supaya UI kasih info ramah
        st.info(f"Analisa belum aktif (STT error: {e}).")
        return ""

# ======================
# UI
# ======================
def show_hafalan_audio_tab():
    st.title("🎙️ Setor Hafalan — Audio")
    st.caption(
        "Fitur ini adalah **simulasi pembelajaran** untuk membantu menyetor bacaan. "
        "Bukan penilaian tajwid resmi dan **bukan fatwa**. "
        "Selalu rujuk & konfirmasi kepada ustadz pembimbing."
    )

    # Pilih surah & range
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

    # ==== State awal ====
    if "setor_audio_bytes" not in st.session_state:
        st.session_state.setor_audio_bytes = None
        st.session_state.setor_audio_name = None
        st.session_state.setor_transcript = None
    
    st.markdown("#### 🎧 Unggah Rekaman Bacaan")
    upload = st.file_uploader(
        "Pilih file audio (mp3/wav/m4a/webm)",
        type=["mp3", "wav", "m4a", "webm"],
        key="audio_upload"
    )
    
    # ==== Sinkronisasi state (tanpa on_change, tanpa st.stop) ====
    if upload is None:
        # user belum upload / klik ❌
        if st.session_state.setor_audio_bytes is not None:
            st.session_state.setor_audio_bytes = None
            st.session_state.setor_audio_name = None
            st.session_state.setor_transcript = None
    else:
        # user pilih file; kalau baru/berbeda -> simpan
        if (
            st.session_state.setor_audio_bytes is None
            or st.session_state.setor_audio_name != upload.name
        ):
            fname, data = _audio_file_meta(upload)
            st.session_state.setor_audio_bytes = data
            st.session_state.setor_audio_name = fname
            st.session_state.setor_transcript = None  # reset transkrip
    
    # ==== Render lanjut hanya jika ada audio di state ====
    if st.session_state.setor_audio_bytes:
        st.audio(st.session_state.setor_audio_bytes, format="audio/*")
        st.success("Rekaman siap. Anda bisa kirim ke ustadz atau gunakan analisa otomatis di bawah.")
    
        # --- Kirim ke WA ---
        tujuan = st.selectbox(
            "Kirim ke:",
            ["Buka WA (pilih kontak sendiri)"] + [u["name"] for u in USTADZ_LIST],
            index=0
        )
        wa = "" if tujuan.startswith("Buka WA") else next((u["wa"] for u in USTADZ_LIST if u["name"] == tujuan), "")
        summary = (
            f"{WA_GREETING}\n"
            f"- Surah: {MUSHAF[surah_key]['name']} ({surah_key})\n"
            f"- Ayat: {start}–{end}\n"
            f"(Audio terlampir)"
        )
        wa_link = wa_prefill_link(wa, summary)
        st.link_button("💬 Kirim ke WhatsApp", wa_link if wa_link else "#", use_container_width=True)
    
        st.divider()

        # ===== Analisa opsional (STT) =====
        with st.expander("🧪 Analisa Otomatis (Opsional)", expanded=False):
            st.caption(
                "Analisa ini bersifat percobaan dan mungkin **tidak akurat**. "
                "Gunakan hanya sebagai bantuan belajar, bukan penilaian tajwid."
            )
            a1, a2 = st.columns([1,1])
            with a1:
                do_transcribe = st.button("▶️ Jalankan Transkripsi (Whisper)")
            with a2:
                if st.session_state.setor_transcript:
                    st.button("🧹 Bersihkan Transkrip", on_click=lambda: st.session_state.update({"setor_transcript": None}))
            if do_transcribe:
                with st.spinner("Memproses audio..."):
                    text = run_stt(st.session_state.setor_audio_bytes)
                if text:
                    st.session_state.setor_transcript = text
                else:
                    st.info("Belum terhubung ke layanan STT atau terjadi kendala. Coba set API key dulu.")
            if st.session_state.setor_transcript:
                st.markdown("**Hasil transkrip (eksperimental):**")
                st.write(st.session_state.setor_transcript)
                st.caption("Catatan: transkrip bisa berbeda dari teks mushaf. Verifikasi ke ustadz pembimbing.")

    else:
        st.info("Unggah rekaman bacaanmu untuk mulai setoran.")
