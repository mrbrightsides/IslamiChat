import streamlit as st
from urllib.parse import quote_plus

NAMA_USTADZ_1 = "Dr. Heri Iskandar, M.Pd"
NAMA_USTADZ_2 = "Sawi Sujarwo, M.Psi"

WA_LINK_1 = "+6289675674860"
WA_LINK_2 = "62xxxxxxxxxx"

DEFAULT_MESSAGE = (
    "Assalamu'alaikum Ustadz, saya ingin bertanya: "
)

# ===============================================================
# Util
# ===============================================================

def _normalize_wa_base(raw: str) -> str:
    """Terima input berupa link penuh atau nomor, lalu hasilkan base URL wa.me.
    Contoh keluaran: "https://wa.me/62xxxxxxxxxx"
    """
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ""
    return f"https://wa.me/{digits}"


def _with_prefill_message(base_url: str, message: str) -> str:
    if not base_url:
        return ""
    sep = '&' if ('?' in base_url) else '?'
    return f"{base_url}{sep}text={quote_plus(message or '')}"


# ===============================================================
# UI — Card komponen
# ===============================================================

def _ustadz_card(nama: str, wa_raw: str, key_prefix: str):
    base = _normalize_wa_base(wa_raw)

    with st.container(border=True):
        st.subheader(nama)
        msg = st.text_area(
            "Tulis pesan (akan diprefill di WhatsApp):",
            value=DEFAULT_MESSAGE,
            key=f"msg_{key_prefix}",
            height=120,
        )

        link = _with_prefill_message(base, msg)

        col1, col2 = st.columns([1, 1])
        with col1:
            disabled = not bool(link)
            try:
                st.link_button("💬 Chat via WhatsApp", link if link else "#", use_container_width=True, disabled=disabled)
            except Exception:
                if disabled:
                    st.button("💬 Chat via WhatsApp (isi nomor dulu)", disabled=True, use_container_width=True)
                else:
                    st.markdown(f"[💬 Chat via WhatsApp]({link})", unsafe_allow_html=True)
        with col2:
            if base:
                st.code(link, language="text")
            else:
                st.info("Isi nomor/tautan WA di konfigurasi untuk mengaktifkan tombol.")


# ===============================================================
# Public API — panggil fungsi ini di tab utama
# ===============================================================

def show_chat_ustadz_tab():
    st.title("📞 Chat Ustadz")
    st.caption(
        "Tulis pesan lalu klik tombol untuk membuka WhatsApp. \n"
        "Catatan: aplikasi ini *tidak* mengirim pesan otomatis; tombol hanya membuka WA dengan pesan terisi."
    )

    c1, c2 = st.columns(2)
    with c1:
        _ustadz_card(NAMA_USTADZ_1, WA_LINK_1, key_prefix="u1")
    with c2:
        _ustadz_card(NAMA_USTADZ_2, WA_LINK_2, key_prefix="u2")

    st.divider()
    with st.expander("⚙️ Konfigurasi ringkas", expanded=False):
        st.write(
            "Ganti nilai `NAMA_USTADZ_1/2` dan `WA_LINK_1/2` di bagian atas file ini.\n"
            "- Jika mengisi nomor, gunakan format internasional tanpa tanda + (contoh: `62xxxxxxxxxx`).\n"
            "- Jika mengisi tautan, boleh `https://wa.me/62...` atau `https://api.whatsapp.com/send?phone=62...`.\n"
            "- Pesan akan di-URL-encode otomatis."
        )
