import io
import csv
import requests
import streamlit as st
from datetime import datetime, date
from typing import Optional, List, Dict

import math
import pandas as pd
import streamlit as st

API_BASE = "https://api.aladhan.com/v1"

def render_simple_hijri_calendar(month_len=30, first_weekday=0, event_days=None, title="Kalender Hijriah"):
    """
    month_len: 29 atau 30 (default 30)
    first_weekday: 0=Senin, 6=Minggu (hanya untuk offset awal kolom)
    event_days: set/list berisi integer hari yang ada event (mis. {2,5,9})
    """
    event_days = set(event_days or [])
    first_weekday = int(first_weekday) % 7
    cells = [""] * first_weekday + list(range(1, month_len + 1))
    # pad sampai kelipatan 7
    if len(cells) % 7 != 0:
        cells += [""] * (7 - (len(cells) % 7))

    rows = []
    for i in range(0, len(cells), 7):
        row = []
        for d in cells[i:i+7]:
            if d == "":
                row.append("")
            else:
                mark = " *" if d in event_days else ""
                row.append(f"{d}{mark}")
        rows.append(row)

    df = pd.DataFrame(rows, columns=["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"])
    st.subheader(title)
    st.table(df)

# ===================== Helpers Tanggal =====================
def _to_iso_gdate(val: str) -> str:
    """
    Normalisasi tanggal gregorian ke ISO (YYYY-MM-DD).
    API kadang mengirim 'DD-MM-YYYY'.
    """
    if not isinstance(val, str):
        return val
    try:
        # Sudah ISO
        if len(val) == 10 and val[4] == '-' and val[7] == '-':
            return val
        # DD-MM-YYYY
        if len(val) == 10 and val[2] == '-' and val[5] == '-':
            dd, mm, yyyy = val.split('-')
            return f"{yyyy}-{mm}-{dd}"
    except Exception:
        pass
    return val

def _safe_fromiso(s: str) -> Optional[date]:
    """Coba parse YYYY-MM-DD; kalau gagal, coba normalize dulu."""
    try:
        return date.fromisoformat(s)
    except Exception:
        try:
            return date.fromisoformat(_to_iso_gdate(s))
        except Exception:
            return None

# ===================== CACHE: API =====================
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

@st.cache_data(ttl=6 * 60 * 60)
def h_to_g_single(dd_mm_yyyy_h: str) -> Optional[dict]:
    """
    Konversi satu tanggal Hijriah (DD-MM-YYYY) ke Gregorian.
    Return: {"gregorian": {"date": "...", "weekday": {"en": ...}}, "hijri": {...}}
    """
    try:
        r = requests.get(f"{API_BASE}/hToG", params={"date": dd_mm_yyyy_h}, timeout=10)
        r.raise_for_status()
        j = r.json()
        if j.get("code") == 200:
            d = j.get("data", {})
            # sebagian response sudah punya struktur g/hijri di level atas
            if isinstance(d, dict) and "gregorian" in d and "hijri" in d:
                return d
            # fallback lain: kadang d langsung "date", dll — abaikan kalau tak lengkap
    except Exception:
        pass
    return None

# ===================== RULES =====================
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
    (9, 1):  "Tāsū‘ā (9 Muharram)",
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
        if not include_tasua and (h_day, h_month_num) == (9, 1):
            pass
        else:
            labels.append(FIXED_EVENTS[(h_day, h_month_num)])
    # ayyam al-bid (selalu ditampilkan)
    if h_day in AYYAM_AL_BID_DAYS:
        labels.append("Ayyām al-Bīḍ (puasa 13–15)")
    # monday-thursday (opsional)
    if include_mon_thu and weekday_en in MON_THU:
        labels.append(MON_THU[weekday_en])
    return labels

# ===================== BUILD KALENDER =====================
@st.cache_data(ttl=6 * 60 * 60)
def build_hijri_year_calendar(year_h: int, include_mon_thu: bool, include_tasua: bool) -> List[Dict]:
    rows: List[Dict] = []
    for m in range(1, 13):
        data = h_to_g_calendar(year_h, m)
        # -------- Fallback kalau bulan ini tidak tersedia dari hToGCalendar --------
        if not data:
            synth_days = set()
            # event tetap yang jatuh di bulan m
            for (d_fixed, m_fixed), _label in FIXED_EVENTS.items():
                if m_fixed == m:
                    synth_days.add(d_fixed)
            # ayyam al-bid 13-15 setiap bulan
            synth_days.update({13, 14, 15})

            for d in sorted(synth_days):
                dd = f"{d:02d}"
                mm = f"{m:02d}"
                yyyy = f"{year_h}"
                payload = h_to_g_single(f"{dd}-{mm}-{yyyy}")
                if not payload:
                    continue
                g = payload.get("gregorian", {})
                h = payload.get("hijri", {})
                try:
                    g_date = _to_iso_gdate(g["date"])
                    w_en = g["weekday"]["en"]
                    h_date = h["date"]
                    h_day = int(h["day"])
                    h_month_num = int(h["month"]["number"])
                    h_month_en = h["month"]["en"]
                except Exception:
                    continue

                lbls = ", ".join(
                    labels_for_day(h_day, h_month_num, w_en, include_mon_thu, include_tasua)
                )
                rows.append({
                    "gregorian": g_date,
                    "weekday": w_en,
                    "hijri": h_date,
                    "h_day": h_day,
                    "h_month_num": h_month_num,
                    "h_month_en": h_month_en,
                    "labels": lbls
                })
            # lanjut ke bulan berikutnya
            continue

        # -------- Jalur normal: pakai hToGCalendar --------
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

            lbls = ", ".join(
                labels_for_day(h_day, h_month_num, w_en, include_mon_thu, include_tasua)
            )
            rows.append({
                "gregorian": g_date,
                "weekday": w_en,
                "hijri": h_date,
                "h_day": h_day,
                "h_month_num": h_month_num,
                "h_month_en": h_month_en,
                "labels": lbls
            })

    rows.sort(key=lambda r: (_safe_fromiso(r["gregorian"]) or date.max))
    return rows

@st.cache_data(ttl=6 * 60 * 60)
def h_to_g_single(dd_mm_yyyy_h: str) -> Optional[dict]:
    """
    Konversi satu tanggal Hijriah (DD-MM-YYYY) ke Gregorian.
    Return: {"gregorian": {"date": "...", "weekday": {"en": ...}}, "hijri": {...}}
    """
    try:
        r = requests.get(f"{API_BASE}/hToG", params={"date": dd_mm_yyyy_h}, timeout=10)
        r.raise_for_status()
        j = r.json()
        if j.get("code") == 200:
            d = j.get("data", {})
            # sebagian response sudah punya struktur g/hijri di level atas
            if isinstance(d, dict) and "gregorian" in d and "hijri" in d:
                return d
            # fallback lain: kadang d langsung "date", dll — abaikan kalau tak lengkap
    except Exception:
        pass
    return None

# ===================== FILTER & UPCOMING =====================
def find_upcoming(rows: List[Dict], from_g: date, limit: int = 5) -> List[Dict]:
    # hanya yang berlabel & >= today
    out = []
    for r in rows:
        if not r.get("labels"):
            continue
        gdt = _safe_fromiso(r["gregorian"])
        if not gdt:
            continue
        if gdt >= from_g:
            delta = (gdt - from_g).days
            out.append({**r, "days_left": delta})
    # sort by tanggal lalu ambil limit
    out.sort(key=lambda r: _safe_fromiso(r["gregorian"]))
    return out[:limit]

def filter_rows(rows: List[Dict], only_labeled: bool, month_filter: Optional[int]) -> List[Dict]:
    res = rows
    if month_filter:
        res = [r for r in res if r["h_month_num"] == month_filter]
    if only_labeled:
        res = [r for r in res if r.get("labels")]
    return res

# ===================== EXPORTERS =====================
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
        if not r.get("labels"):
            continue
        y, m, d = _to_iso_gdate(r["gregorian"]).split("-")
        dt = f"{y}{m}{d}"
        summary = r["labels"].split(",")[0].strip()  # ambil label pertama
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

# ===================== UI =====================
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
        year_h = st.number_input(
            "Tahun Hijriah", value=h_year, step=1, min_value=h_year - 3, max_value=h_year + 3
        )
    with c2:
        include_mon_thu = st.toggle("Tandai puasa Senin & Kamis", value=True)
    with c3:
        include_tasua = st.toggle("Tandai Tāsū‘ā (9 Muharram)", value=True)
    with c4:
        only_labeled = st.checkbox("Tampilkan hanya hari bertanda (event/puasa)", value=False)

    # Build calendar (butuh helper yang sudah ada di modulmu)
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
        st.caption(
            "Belum ada event terdekat yang terdaftar. Aktifkan penanda Senin/Kamis atau Tāsū‘ā/‘Āsyūrā’ untuk melihat jadwal."
        )

    # View mode: tahun penuh / bulan tertentu
    st.subheader("📋 Kalender")
    vm1, _ = st.columns([1, 3])
    options_vals = [0] + list(range(1, 13))
    default_val = h_month_num if int(year_h) == h_year else 0
    default_idx = options_vals.index(default_val)

    with vm1:
        view_month = st.selectbox(
            "Tampilan bulan (opsional)",
            options=options_vals,
            format_func=lambda x: "Tahun penuh" if x == 0 else f"Bulan {x}",
            index=default_idx,
            help="Pilih 'Tahun penuh' atau salah satu bulan Hijriah.",
        )

    filtered = filter_rows(
        rows,
        only_labeled=only_labeled,
        month_filter=view_month if view_month != 0 else None,
    )

    # ---- Fallback isi bulan kalau filter kosong ----
    if not filtered:
        month_len = 30
        skeleton = []
        if view_month != 0:
            for d in range(1, month_len + 1):
                dd = f"{d:02d}"
                mm = f"{int(view_month):02d}"
                yyyy = str(int(year_h))
                payload = h_to_g_single(f"{dd}-{mm}-{yyyy}")
                if not payload:
                    skeleton.append(
                        {
                            "gregorian": "—",
                            "weekday": "",
                            "hijri": f"{dd}-{mm}-{yyyy} H",
                            "h_month_en": "",
                            "labels": "",
                        }
                    )
                    continue
                g = payload.get("gregorian", {})
                h = payload.get("hijri", {})
                skeleton.append(
                    {
                        "gregorian": _to_iso_gdate(g.get("date", "—")),
                        "weekday": g.get("weekday", {}).get("en", ""),
                        "hijri": h.get("date", f"{dd}-{mm}-{yyyy} H"),
                        "h_month_en": h.get("month", {}).get("en", ""),
                        "labels": "",
                    }
                )
            filtered = skeleton
        else:
            filtered = [
                {
                    "gregorian": "—",
                    "weekday": "",
                    "hijri": f"{year_h} H",
                    "h_month_en": "",
                    "labels": "Data tahun penuh tidak tersedia",
                }
            ]

    # ---- Dari list -> DataFrame ----
    import pandas as pd
    df = pd.DataFrame(filtered, columns=["gregorian", "weekday", "hijri", "h_month_en", "labels"])

    # ---- Helpers untuk label ----
    def _parse_hijri_day(hijri_str: str):
        try:
            return int(str(hijri_str).split("-")[0])
        except Exception:
            return None

    def add_event_labels(df_in: pd.DataFrame, mark_mk: bool, mark_tasua: bool) -> pd.DataFrame:
        if df_in is None or df_in.empty:
            return df_in
        df2 = df_in.copy()
        lab = []
        for _, r in df2.iterrows():
            tags = []
            if mark_mk:
                wd = str(r.get("weekday", "")).strip()
                if wd == "Monday":
                    tags.append("Puasa Senin")
                elif wd == "Thursday":
                    tags.append("Puasa Kamis")
            if mark_tasua:
                dnum = _parse_hijri_day(r.get("hijri", ""))
                hme = str(r.get("h_month_en", "")).lower()
                if dnum == 9 and hme == "muharram":
                    tags.append("Tasū‘a (9 Muharram)")
            lab.append(", ".join(tags))
        df2["labels"] = lab
        return df2

    # Tambahkan label sesuai toggle
    df = add_event_labels(df, include_mon_thu, include_tasua)

    # Filter hanya bertanda jika dicentang
    if only_labeled:
        df = df[df["labels"].astype(str).str.len() > 0]

    # Render tabel final (satu saja, jangan dua-duanya)
    st.dataframe(df[["gregorian", "weekday", "hijri", "h_month_en", "labels"]],
                 use_container_width=True, height=420)

    # Downloads (export pakai list of dicts)
    export_rows = df.to_dict("records")
    cold1, cold2 = st.columns([1, 1])
    with cold1:
        st.download_button(
            "⬇️ Unduh CSV Kalender (sesuai tampilan)",
            data=to_csv_bytes(export_rows),
            file_name=f"kalender_hijriah_{year_h}{('_bulan'+str(view_month)) if view_month else ''}.csv",
            mime="text/csv",
        )
    with cold2:
        st.download_button(
            "📥 Ekspor .ICS (Google/Apple/Outlook)",
            data=to_ics_bytes(export_rows),
            file_name=f"kalender_hijriah_{year_h}{('_bulan'+str(view_month)) if view_month else ''}.ics",
            mime="text/calendar",
        )

    st.caption("Catatan: kalender berdasar perhitungan (Umm al-Qura) – bisa bergeser ±1 hari dari rukyat lokal.")
