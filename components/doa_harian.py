import requests, streamlit as st

API_BASE = "https://equran.id/api/doa"
CACHE_TTL = 60 * 60 * 12  # 12 jam

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_api(grup: str | None = None, tag: str | None = None):
    params = {}
    if grup: params["grup"] = grup
    if tag:  params["tag"]  = tag

    r = requests.get(API_BASE, params=params, timeout=15)
    r.raise_for_status()
    raw = r.json()

    # --- Normalisasi respons agar selalu list[dict] ---
    rows = raw
    if isinstance(raw, dict):
        # kalau API berbentuk {"data":[...]} atau mirip
        if "data" in raw and isinstance(raw["data"], list):
            rows = raw["data"]
        # kalau payloadnya salah satu kunci menyimpan list
        elif any(isinstance(v, list) for v in raw.values()):
            for v in raw.values():
                if isinstance(v, list):
                    rows = v
                    break

    if isinstance(rows, dict):
        rows = [rows]

    norm_rows: list[dict] = []
    for x in rows:
        if isinstance(x, dict):
            norm_rows.append(x)
        else:
            norm_rows.append({"judul": str(x), "arab": "", "latin": "", "indo": "", "grup": "Lainnya"})

    return norm_rows

def safe_get(d: dict, key: str, default=""):
    return d.get(key, default) if isinstance(d, dict) else default

def show_doa_harian():
    st.title("📖 Doa Harian (EQuran.id API)")

    data = fetch_api()

    if not data:
        st.warning("Tidak ada data doa ditemukan.")
        return

    # Pastikan setiap item minimal berbentuk dict dengan kunci standar
    fixed = []
    for x in data:
        fixed.append({
            "id":    safe_get(x, "id"),
            "grup":  safe_get(x, "grup", "Tanpa Grup"),
            "judul": safe_get(x, "doa",  safe_get(x, "judul", "Tanpa judul")),
            "arab":  safe_get(x, "ayat", safe_get(x, "arab", "")),
            "latin": safe_get(x, "latin", ""),
            "indo":  safe_get(x, "artinya", safe_get(x, "indo", "")),
            "audio": safe_get(x, "audio"),
        })

    # --- Kategori unik ---
    grups = sorted({ item["grup"] if item["grup"] else "Tanpa Grup" for item in fixed })
    grup  = st.selectbox("Kategori", grups)

    # --- Filter sesuai grup ---
    items = [d for d in fixed if (d["grup"] or "Tanpa Grup") == grup]
    if not items:
        st.info("Tidak ada doa pada kategori ini.")
        return

    # --- Pilihan doa ---
    opt_titles = [d["judul"] or f"Tanpa judul #{d['id']}" for d in items]
    opt = st.selectbox("Pilih doa", opt_titles)
    doa = next(d for d in items if (d["judul"] or f"Tanpa judul #{d['id']}") == opt)

    # --- Tampilkan konten ---
    st.subheader(doa["judul"] or "Tanpa judul")
    st.markdown(f"**Arab:**\n\n{doa['arab'] or '-'}")
    st.markdown(f"**Latin:**\n\n{doa['latin'] or '-'}")
    st.info(f"**Arti:** {doa['indo'] or '-'}")
    st.caption("Sumber: EQuran.id")

    # tombol copy
    copy_button(f"{doa['arab']}\n\n{doa['latin']}\n\n{doa['indo']}")

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_doa_by_id(doa_id: int):
    r = requests.get(f"{API_BASE}/{doa_id}", timeout=15)
    r.raise_for_status()
    raw = r.json()
    if isinstance(raw, dict) and "data" in raw:
        raw = raw["data"]
    if not isinstance(raw, dict):
        return None
    return {
        "id":    raw.get("id"),
        "grup":  raw.get("grup", "Tanpa Grup"),
        "judul": raw.get("doa") or raw.get("judul", "Tanpa judul"),
        "arab":  raw.get("ayat") or raw.get("arab", ""),
        "latin": raw.get("latin", ""),
        "indo":  raw.get("artinya") or raw.get("indo", ""),
        "audio": raw.get("audio"),
    }
