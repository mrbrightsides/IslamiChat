import random
import requests
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple

API = "https://equran.id/api/v2"

# =========================
# JUZ MAP (pembuka Juz → (surah, ayat))
# Sumber: standar mushaf Madinah (bisa di-tweak kalau mau pakai mapping lain)
# =========================
JUZ_STARTS: Dict[int, Tuple[int, int]] = {
    1:(1,1),  2:(2,142), 3:(2,253), 4:(3,93),  5:(4,24),
    6:(4,148),7:(5,82),  8:(6,111), 9:(7,88), 10:(8,41),
    11:(9,93),12:(11,6), 13:(12,53),14:(15,1), 15:(17,1),
    16:(18,75),17:(21,1),18:(23,1), 19:(25,21),20:(27,56),
    21:(29,46),22:(33,31),23:(36,28),24:(39,32),25:(41,47),
    26:(46,1), 27:(51,31),28:(58,1), 29:(67,1), 30:(78,1),
}

# =========================
# Data fetchers (cached)
# =========================
@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def list_surah() -> List[Dict[str, Any]]:
    r = requests.get(f"{API}/surat", timeout=12)
    r.raise_for_status()
    j = r.json()
    return j.get("data", []) or j.get("Data", []) or []

@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def get_surah_detail(no: int) -> Dict[str, Any]:
    r = requests.get(f"{API}/surat/{no}", timeout=15)
    r.raise_for_status()
    j = r.json()
    return j.get("data", {}) or j.get("Data", {}) or {}

@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def get_tafsir(no: int) -> Dict[str, Any]:
    r = requests.get(f"{API}/tafsir/{no}", timeout=15)
    r.raise_for_status()
    j = r.json()
    return j.get("data", {}) or j.get("Data", {}) or {}

# =========================
# Utilities
# =========================
def _audio_full_candidates(detail: Dict[str, Any]) -> Dict[str, str]:
    cands: Dict[str, str] = {}
    af = detail.get("audioFull") or detail.get("audio_full") or (detail.get("audio") or {}).get("full")
    if isinstance(af, dict):
        for k, v in af.items():
            if isinstance(v, str) and v.strip():
                cands[str(k)] = v
    elif isinstance(af, list):
        for i, url in enumerate(af, 1):
            if isinstance(url, str) and url.strip():
                cands[f"Qari {i}"] = url
    elif isinstance(af, str) and af.strip():
        cands["Default"] = af
    return cands

def _normalize_ayat(a: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "nomor": a.get("nomorAyat") or a.get("nomor") or a.get("number"),
        "arab": a.get("teks") or a.get("arab") or a.get("text") or "",
        "latin": a.get("teks_latin") or a.get("latin") or a.get("read") or "",
        "terjemah": a.get("teks_id") or a.get("terjemah") or a.get("translation") or "",
        "audio": a.get("audio") or a.get("audio_url") or "",
    }

def _ayat_list(detail: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = detail.get("ayat") or detail.get("verses") or []
    return [_normalize_ayat(a) for a in raw]

def _get_last_state() -> Dict[str, int]:
    return st.session_state.setdefault("quran_last", {"surah": 1, "ayat": 1})

def _set_last_state(surah: int, ayat: int) -> None:
    st.session_state["quran_last"] = {"surah": int(surah), "ayat": int(ayat)}

def _hafalan_state() -> Dict[str, Any]:
    # { "items": [(surah, ayat), ...], "repeat": 3, "hide_trans": True, "shuffle": False }
    return st.session_state.setdefault("q_hafalan", {"items": [], "repeat": 3, "hide_trans": True, "shuffle": False})

def _add_hafalan(surah: int, ayat: int):
    st.session_state.setdefault("q_hafalan", {"items": [], "repeat": 3, "hide_trans": True, "shuffle": False})
    key = (int(surah), int(ayat))
    if key not in st.session_state["q_hafalan"]["items"]:
        st.session_state["q_hafalan"]["items"].append(key)

def _remove_hafalan(surah: int, ayat: int):
    state = _hafalan_state()
    state["items"] = [x for x in state["items"] if x != (int(surah), int(ayat))]

# =========================
# Main Renderer
# =========================
def render_quran_tab():
    st.header("📖 Al-Qur’an")
    st.caption("Sumber data: EQuran.id • Teks/tafsir Kemenag • Audio via CDN")

    # --- Lanjutkan bacaan terakhir
    last = _get_last_state()
    with st.expander("⏭️ Lanjutkan bacaan terakhir", expanded=False):
        st.write(f"Terakhir: **Surah {last['surah']}** ayat **{last['ayat']}**")
        if st.button("Buka posisi terakhir", use_container_width=True):
            st.session_state["__sf_q_surah"] = last["surah"]
            st.session_state["__sf_scroll_to_ayat"] = last["ayat"]

    # --- Daftar surat
    try:
        surat_list = list_surah()
    except Exception as e:
        st.error(f"Gagal memuat daftar surat: {e}")
        return

    options = {
        f"{s.get('nomor'):>03} — {s.get('nama_latin','')} ({s.get('jumlah_ayat','?')} ayat)": s.get("nomor")
        for s in surat_list
    }
    default_surah = st.session_state.get("__sf_q_surah", 1)
    label_idx = list(options.values()).index(default_surah) if default_surah in options.values() else 0
    pilih_label = st.selectbox("Pilih Surat", list(options.keys()), index=label_idx, key="__sf_q_surah_label")
    no_surah = options[pilih_label]

    # --- Navigasi Juz
    with st.expander("🧭 Navigasi Juz (beta)", expanded=False):
        colj1, colj2 = st.columns([2,1])
        with colj1:
            juz = st.selectbox("Pilih Juz", list(range(1,31)), key="__sf_q_juz")
        with colj2:
            if st.button("Lompat ke Juz", use_container_width=True):
                s, a = JUZ_STARTS.get(juz, (1,1))
                st.session_state["__sf_q_surah"] = s
                st.session_state["__sf_q_surah_label"] = None
                st.session_state["__sf_scroll_to_ayat"] = a
                # force re-render ke surah tujuan
                st.experimental_rerun()

        st.caption("Mapping mengikuti pembuka Juz pada mushaf Madinah; bisa disesuaikan bila perlu.")

    # --- Detail surat
    try:
        detail = get_surah_detail(int(no_surah))
    except Exception as e:
        st.error(f"Gagal memuat detail surat: {e}")
        return

    nama_latin = detail.get("nama_latin") or detail.get("namaLatin") or detail.get("nama", "")
    nama_arab  = detail.get("nama") or ""
    info = f"{detail.get('tempat_turun','')} • {detail.get('arti','')} • {detail.get('jumlah_ayat','?')} ayat"
    top = st.columns([3, 2])
    with top[0]:
        st.subheader(f"{nama_latin} — {nama_arab}")
        st.caption(info)

    cands = _audio_full_candidates(detail)
    with top[1]:
        if cands:
            qari_names = list(cands.keys())
            qari = st.selectbox("Audio full surat (qari)", qari_names, key="__sf_q_qari")
            st.audio(cands[qari])

    # --- Pencarian dalam surat
    q = st.text_input("Cari ayat (nomor / potongan teks terjemah/Arab)", key="__sf_q_query")

    # --- Render ayat
    ayat_all = _ayat_list(detail)
    if q:
        ql = q.strip().lower()
        def match(a):
            return (
                ql == str(a["nomor"]).lower() or
                ql in a["terjemah"].lower() or
                ql in a["arab"].lower()
            )
        ayat_all = [a for a in ayat_all if match(a)]

    scroll_target = st.session_state.pop("__sf_scroll_to_ayat", None)

    for a in ayat_all:
        n = a["nomor"]
        with st.container():
            st.markdown(f"**{n}**")
            st.markdown(
                f"<div style='font-size:1.5rem; line-height:2.2rem; direction:rtl; text-align:right;'>{a['arab']}</div>",
                unsafe_allow_html=True
            )

            # Controls tampilan
            show_latin = st.toggle("Latin", value=False, key=f"latin_{no_surah}_{n}")
            show_id = st.toggle("Terjemah", value=True, key=f"id_{no_surah}_{n}")

            if show_latin and a["latin"]:
                st.caption(a["latin"])
            if show_id and a["terjemah"]:
                st.write(a["terjemah"])

            # Audio per-ayat
            if a["audio"]:
                st.audio(a["audio"])

            c1, c2, c3 = st.columns(3)
            if c1.button(f"Tandai terakhir di {n}", key=f"mark_{n}"):
                _set_last_state(no_surah, n)
                st.success(f"Disimpan: Surah {no_surah}, ayat {n}", icon="✅")

            # Hafalan: add/remove
            in_list = (int(no_surah), int(n)) in _hafalan_state()["items"]
            if not in_list:
                if c2.button("➕ Hafalan", key=f"hafal_add_{n}"):
                    _add_hafalan(no_surah, n)
                    st.toast(f"Ditambahkan ke daftar hafalan: {no_surah}:{n}")
            else:
                if c2.button("➖ Hapus Hafalan", key=f"hafal_del_{n}"):
                    _remove_hafalan(no_surah, n)
                    st.toast(f"Dihapus dari daftar hafalan: {no_surah}:{n}")

            c3.write("")  # spacer
            st.divider()

            if scroll_target and int(n) == int(scroll_target):
                st.info(f"📌 Anda di ayat {n}.", icon="📌")

    # --- Tafsir
    with st.expander("📚 Tampilkan Tafsir Surat ini", expanded=False):
        try:
            tafsir = get_tafsir(int(no_surah))
            konten = tafsir.get("tafsir") or tafsir.get("keterangan") or tafsir
            if isinstance(konten, list):
                for item in konten:
                    st.markdown(f"**Ayat {item.get('ayat','?')}**")
                    st.write(item.get("teks") or item.get("text") or "")
                    st.divider()
            else:
                if isinstance(konten, dict):
                    for k, v in konten.items():
                        st.markdown(f"**{k}**")
                        st.write(v)
                else:
                    st.write(konten)
        except Exception as e:
            st.warning(f"Tafsir tidak tersedia: {e}")

    # --- MODE HAFALAN
    st.subheader("🧠 Mode Hafalan")
    h = _hafalan_state()
    colh1, colh2, colh3, colh4 = st.columns([1,1,1,1])
    with colh1:
        h["repeat"] = st.number_input("Ulangi tiap ayat", min_value=1, max_value=20, value=h.get("repeat",3), step=1)
    with colh2:
        h["hide_trans"] = st.checkbox("Sembunyikan terjemah/latin", value=h.get("hide_trans", True))
    with colh3:
        h["shuffle"] = st.checkbox("Acak urutan", value=h.get("shuffle", False))
    with colh4:
        if st.button("Kosongkan daftar"):
            h["items"] = []
            st.toast("Daftar hafalan dikosongkan.")

    items = h["items"][:]
    if h["shuffle"]:
        random.shuffle(items)

    if not items:
        st.info("Belum ada ayat di daftar hafalan. Gunakan tombol **➕ Hafalan** pada ayat di atas.")
        return

    # Render latihan
    for (s, n) in items:
        try:
            d = get_surah_detail(s)
            ayat = next((x for x in _ayat_list(d) if int(x["nomor"]) == int(n)), None)
        except Exception:
            ayat = None

        box = st.container()
        with box:
            st.markdown(f"**{s}:{n}**")
            if ayat:
                st.markdown(
                    f"<div style='font-size:1.6rem; line-height:2.4rem; direction:rtl; text-align:right;'>{ayat['arab']}</div>",
                    unsafe_allow_html=True
                )
                if not h["hide_trans"]:
                    if ayat["latin"]:
                        st.caption(ayat["latin"])
                    if ayat["terjemah"]:
                        st.write(ayat["terjemah"])

                # Repeat counter sederhana
                reps_key = f"reps_{s}_{n}"
                cur = st.session_state.get(reps_key, 0)
                cols = st.columns([1,1,3])
                if cols[0].button("Ulangi +1", key=f"btn_inc_{s}_{n}"):
                    cur += 1
                if cols[1].button("Reset", key=f"btn_res_{s}_{n}"):
                    cur = 0
                st.session_state[reps_key] = cur
                st.progress(min(cur / max(h['repeat'],1), 1.0), text=f"Ulangan: {cur}/{h['repeat']}")

                if ayat["audio"]:
                    st.audio(ayat["audio"])
            else:
                st.warning("Ayat tidak ditemukan (cek koneksi/API).")
            st.divider()
