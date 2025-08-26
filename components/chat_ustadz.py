import streamlit as st
from urllib.parse import quote_plus

# ==== Konfigurasi ====
NAMA_USTADZ_1   = "Dr. Heri Iskandar, M.Pd"
PROFIL_USTADZ_1 = "Pengasuh MT Al Hikam Palembang. Fokus fikih ibadah & pendidikan."
WA_LINK_1       = "+6289675674860"
DEFAULT_MSG_1   = "Assalamu'alaikum Ustadz, mohon bimbingannya terkait pertanyaan saya."
FOTO_USTADZ_1   = "https://i.imgur.com/KymF9yk.png"
JAM_CHAT_1      = "Senin–Jumat: 19.30–21.00 WIB atau ba'da Ashar sampai sebelum Maghrib"

NAMA_USTADZ_2   = "Sawi Sujarwo, S.Psi., M.A"
PROFIL_USTADZ_2 = "Psikolog dan cendekiawan muslim. Fokus parenting, remaja, dan kesehatan mental."
WA_LINK_2       = "+6281377544596"
DEFAULT_MSG_2   = "Assalamu'alaikum Ustadz, saya ingin konsultasi singkat."
FOTO_USTADZ_2   = "https://i.imgur.com/NMw3m9V.png"
JAM_CHAT_2      = "Senin-Jumat: 09.00–11.00 WIB, 19.30–21.00 WIB"

# ==== Utils ====
def _normalize_wa_base(raw: str) -> str:
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    digits = "".join(ch for ch in raw if ch.isdigit())
    return f"https://wa.me/{digits}" if digits else ""

def _with_prefill_message(base_url: str, message: str) -> str:
    if not base_url:
        return ""
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}text={quote_plus(message or '')}"

# ==== Card Ustadz ====
def _ustadz_card(nama: str, profil: str, wa_raw: str, default_msg: str, foto_url: str = None, jam_chat: str = None):
    base = _normalize_wa_base(wa_raw)
    link = _with_prefill_message(base, default_msg)

    with st.container(border=True):
        if foto_url:
            st.image(foto_url, width=120)

        st.subheader(nama)
        if profil:
            st.caption(profil)  

        if jam_chat:
            st.markdown(f"🕒 **Jam Chat:** {jam_chat}")  

        disabled = not bool(link)
        try:
            st.link_button("💬 Chat via WhatsApp", link if link else "#",
                           use_container_width=True, disabled=disabled)
        except Exception:
            if disabled:
                st.button("💬 Chat via WhatsApp (isi nomor dulu)",
                          disabled=True, use_container_width=True)
            else:
                st.markdown(f"[💬 Chat via WhatsApp]({link})", unsafe_allow_html=True)

# ==== Tab utama ====
def show_chat_ustadz_tab():
    st.title("📞 Chat Ustadz")
    st.caption(
        "Klik tombol untuk membuka WhatsApp dengan pesan awal. "
        "Catatan: aplikasi ini **tidak** mengirim pesan otomatis. "
        "Mohon hargai waktu. Jangan menghubungi di luar jam yang tertera."
    )

    _ustadz_card(NAMA_USTADZ_1, PROFIL_USTADZ_1, WA_LINK_1, DEFAULT_MSG_1, FOTO_USTADZ_1, JAM_CHAT_1)
    st.markdown("---")
    _ustadz_card(NAMA_USTADZ_2, PROFIL_USTADZ_2, WA_LINK_2, DEFAULT_MSG_2, FOTO_USTADZ_2, JAM_CHAT_2)
