import io
import csv
import requests
import streamlit as st
from datetime import datetime, date
from typing import Optional, List, Dict

API_BASE = "https://api.aladhan.com/v1"

def _to_iso_gdate(val: str) -> str:
    """
    Normalisasi tanggal gregorian ke ISO (YYYY-MM-DD).
    API kadang mengirim 'DD-MM-YYYY'.
    """
    if not isinstance(val, str):
        return val
    try:
        if len(val) == 10 and val[4] == '-' and val[7] == '-':
            return val
        if len(val) == 10 and val[2] == '-' and val[5] == '-':
            dd, mm, yyyy = val.split('-')
            return f"{yyyy}-{mm}-{dd}"
    except Exception:
        pass
    return val

# ========== CACHE HELPERS ==========
@st.cache_data(ttl=6 * 60 * 60)
def g_to_h(date_dd_mm_yyyy: str) -> Optional[dict]:
    """Konversi Gregorian → Hijri (satu hari). Param harus DD-MM-YYYY."""
    try:
        r = requests.get(f"{API_BASE}/gToH", params={"date": date_dd_mm_yyyy}, timeout=10)
        r.raise_for_status()
        j = r.json()
        if j.get("code") == 200:
            d = j.get("data", {})
            if "hijri" in d:
                return d["hijri"]
            return d
    except Exception as e:
        st.error(f"Gagal memuat tanggal Hijriah: {e}")
    return None

@st.cache_data(ttl=6 * 60 * 60)
def h_to_g_calendar(year_h: int, month_h: int) -> Optional[List[dict]]:
    """Ambil kalender 1 bulan Hijri → list item {'hijri':..., 'gregorian':...}."""
    try:
        url = f"{API_BASE}/hToGCalendar/{year_h}/{month_h}"
        r = requests.get(url, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        j = r.json()
        if j.get("code") == 200 and isinstance(j.get("data"), list):
            return j["data"]
    except Exception as e:
        st.warning(f"Gagal ambil kalender H{year_h}/{month_h}: {e}")
    return None

# ========== EVENT RULES ==========
FIXED_EVENTS = {
    # Ramadan
    (1, 9):  "Awal Ramadhan",
    (17, 9): "Nuzulul Qur'an",
    # Rajab
    (27, 7): "Isra' Mi'raj",
    # Rabi' al-awwal
    (12, 3): "Maulid Nabi",
    # Syawal
    (1, 10): "Idul Fitri",
    # Dzulhijjah
    (8, 12): "Tarwiyah",
    (9, 12): "Arafah",
    (10, 12): "Idul Adha",
    # Muharram
    (10, 1): "‘Āsyūrā’ (10 Muharram)",
    (9, 1):  "Tāsū‘ā (9 Muharram)",   # opsional, bisa di-hide via toggle jika mau
}

AYYAM_AL_BID_DAYS = {13, 14, 15}
MON_THU = {"Monday": "Puasa Senin", "Thursday": "Puasa Kamis"}

def labels_for_day(
    h_day: int,
    h_month_num: int,
    weekday_en: str,
    include_mon_thu: bool,
    include_tasua: bool
) -> List[str]:
    labels = []
    # fixed events
    if (h_day, h_month_num) in FIXED_EVENTS:
        # kalau user tidak ingin menampilkan Tasu'a, skip (9 Muharram)
        if not include_tasua and (h_day, h_month_num) == (9, 1):
            pass
        else:
            labels.append(FIXED_EVENTS[(h_day, h_month_num)])
    # ayyam al-bid
    if h_day in AYYAM_AL_BID_DAYS:
        labels.append("Ayyām al-Bīḍ (puasa 13–15)")
    # monday-thursday
    if include_mon_thu and weekday_en in MON_THU:
        labels.append(MON_THU[weekday_en])
    return labels

# ========== BUILD CALENDAR ==========
@st.cache_data(ttl=6 * 60 * 60)
def build_hijri_year_calendar(year_h: int, include_mon_thu: bool, include_tasua: bool) -> List[Dict]:
    rows: List[Dict] = []
    for m in range(1, 13):
        data = h_to_g_calendar(year_h, m)
        if not data:
            continue
        for item in data:
            h = item.get("hijri", {})
            g = item.get("gregorian", {})
            try:
                g_date = _to_iso_gdate(g["date"])
                h_date = h["date"]
                h_day = int(h["day"])
                h_month_num = int(h["month"]["number"])
                h_month_en = h["month"]["en"]
                w_en = g["weekday"]["en"]
            except Exception:
                continue

            lbls = ", ".join(labels_for_day(h_day, h_month_num, w_en, include_mon_thu, include_tasua))
            rows.append({
                "gregorian": g_date,
                "weekday": w_en,
                "hijri": h_date,
                "h_day": h_day,
                "h_month_num": h_month_num,
                "h_month_en": h_month_en,
                "labels": lbls
            })
    rows.sort(key=lambda r: r["gregorian"])
    return rows

# ========== FILTERS & UPCOMING ==========
def find_upcoming(rows: List[Dict], from_g: date, limit: int = 5) -> List[Dict]:
    out = []
    for r in rows:
        if not r["labels"]:
            continue
        g = date.fromisoformat(r["gregorian"])
        if g >= from_g:
            delta = (g - from_g).days
            r = {**r, "days_left": delta}
            out.append(r)
        if len(out) >= limit:
            break
    return out

def filter_rows(rows: List[Dict], only_labeled: bool, month_filter: Optional[int]) -> List[Dict]:
    res = rows
    if only_labeled:
        res = [r for r in res if r["labels"]]
    if month_filter:
        res = [r for r in res if r["h_month_num"] == month_filter]
    return res

# ========== EXPORTERS ==========
def to_csv_bytes(rows: List[Dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "gregorian", "weekday", "hijri", "h_day", "h_month_num", "h_month_en", "labels"
    ])
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return buf.getvalue().encode("utf-8")

def to_ics_bytes(rows: List[Dict]) -> bytes:
    """
    Ekspor event bertanda ke iCalendar (.ics) sebagai all-day events.
    """
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//IslamiChat//Kalender Hijriah//ID"]
    for r in rows:
        if not r["labels"]:
            continue
        y, m, d = _to_iso_gdate(r["gregorian"]).split("-")
        dt = f"{y}{m}{d}"
        summary = r["labels"].split(",")[0]  # ambil label pertama
        desc = f"Hijri: {r['hijri']} ({r['h_month_en']})\\nSemua label: {r['labels']}"
        uid = f"{dt}-{summary.replace(' ', '')}-{r['hijri']}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTART;VALUE=DATE:{dt}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT"
        ]
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines)).encode("utf-8")

# ========== UI ==========
def render_event():
    st.header("📅 Kalender Islam")

    # Hari ini
    today_display = datetime.today().strftime("%Y-%m-%d")
    st.write(f"Hari ini (Masehi): `{today_display}`")

    today_for_api = datetime.today().strftime("%d-%m-%Y")
    hijri = g_to_h(today_for_api)
    if not hijri:
        st.error("Tidak bisa mendapatkan konversi Hijriah dari API.")
        return

    try:
        h_day = int(hijri["day"])
        h_month_num = int(hijri["month"]["number"])
        h_month_en = hijri["month"]["en"]
        h_weekday_ar = hijri["weekday"]["ar"]
        h_date_str = hijri["date"]
        h_year = int(hijri["year"])
    except Exception as e:
        st.error(f"Format data Hijriah tak terduga: {e}")
        return

    st.success(f"Hari ini (Hijri): **{h_weekday_ar}, {h_date_str} {h_month_en} H**")

    # Controls
    st.subheader("⚙️ Pengaturan Tampilan")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        year_h = st.number_input("Tahun Hijriah", value=h_year, step=1, min_value=h_year - 3, max_value=h_year + 3)
    with c2:
        include_mon_thu = st.toggle("Tandai puasa Senin & Kamis", value=True)
    with c3:
        include_tasua = st.toggle("Tandai Tāsū‘ā (9 Muharram)", value=True)
    with c4:
        only_labeled = st.checkbox("Tampilkan hanya hari bertanda (event/puasa)", value=False)

    # Build calendar
    rows = build_hijri_year_calendar(int(year_h), include_mon_thu, include_tasua)
    if not rows:
        st.warning("Kalender tahun ini belum tersedia lengkap dari API.")
        return

    # Upcoming
    st.subheader("🗓️ Event Terdekat")
    ups = find_upcoming(rows, from_g=date.today(), limit=8)
    if ups:
        for r in ups:
            left_txt = f" (tinggal {r['days_left']} hari)" if r["days_left"] > 0 else " (hari ini)"
            st.write(f"- **{r['labels']}** — {r['gregorian']} (Hijri: {r['hijri']} / {r['h_month_en']}){left_txt}")
    else:
        st.caption("Belum ada event terdekat yang terdaftar.")

    # View mode: tahun penuh / bulan tertentu
    st.subheader("📋 Kalender")
    vm1, vm2 = st.columns([1, 2])
    with vm1:
        view_month = st.selectbox(
            "Tampilan bulan (opsional)",
            options=[0] + list(range(1, 13)),
            format_func=lambda x: "Tahun penuh" if x == 0 else f"Bulan {x}",
            index=(h_month_num if year_h == h_year else 0),
            help="Pilih 'Tahun penuh' atau salah satu bulan Hijriah."
        )

    filtered = filter_rows(rows, only_labeled=only_labeled, month_filter=view_month if view_month != 0 else None)

    show_cols = ["gregorian", "weekday", "hijri", "h_month_en", "labels"]
    st.dataframe([{k: r[k] for k in show_cols} for r in filtered], use_container_width=True, height=420)

    # Downloads
    cold1, cold2 = st.columns([1, 1])
    with cold1:
        st.download_button(
            "⬇️ Unduh CSV Kalender (sesuai tampilan)",
            data=to_csv_bytes(filtered),
            file_name=f"kalender_hijriah_{year_h}{'_bulan'+str(view_month) if view_month else ''}.csv",
            mime="text/csv",
        )
    with cold2:
        st.download_button(
            "📥 Ekspor .ICS (Google/Apple/Outlook)",
            data=to_ics_bytes(filtered),
            file_name=f"kalender_hijriah_{year_h}{'_bulan'+str(view_month) if view_month else ''}.ics",
            mime="text/calendar",
        )

    st.caption("Catatan: kalender berdasar perhitungan (Umm al-Qura) – bisa bergeser ±1 hari dari rukyat lokal.")
