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

from typing import List

def labels_for_day(
    h_day: int,
    h_month_num: int,
    weekday_en: str,
    include_mon_thu: bool,
    include_tasua: bool,
) -> List[str]:
    labels: List[str] = []

    # --- Normalisasi ---
    try:
        d = int(h_day)
        m = int(h_month_num)
    except Exception:
        return labels  # kalau datanya aneh, jangan paksa

    w = (weekday_en or "").strip()  # buang spasi

    # --- Fixed events (Tasū‘ā, ‘Āsyūrā, dst) ---
    if (d, m) in FIXED_EVENTS:
        if include_tasua or (d, m) != (9, 1):  # (9,1)=Tasū‘ā
            labels.append(FIXED_EVENTS[(d, m)])

    # --- Ayyām al-Bīḍ (selalu tampil) ---
    if d in AYYAM_AL_BID_DAYS:
        labels.append("Ayyām al-Bīḍ (13–15)")

    # --- Senin/Kamis (opsional) ---
    if include_mon_thu and w in MON_THU:
        labels.append(MON_THU[w])

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
        lab = r.get("labels", [])
        if isinstance(lab, list):
            r_out = {**r, "labels": ", ".join(lab)}
        else:
            r_out = r
        writer.writerow(r_out)
    return buf.getvalue().encode("utf-8")

def to_ics_bytes(rows: List[Dict]) -> bytes:
    """
    Ekspor event bertanda ke iCalendar (.ics) sebagai all-day events.
    """
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//IslamiChat//Kalender Hijriah//ID"]
    for r in rows:
        lab = r.get("labels")
        if not lab:
            continue

        # Normalisasi labels -> string ringkas + gabungan
        if isinstance(lab, list):
            first_label = lab[0] if lab else ""
            all_labels = ", ".join(lab)
        else:  # string
            first_label = lab.split(",")[0].strip()
            all_labels = lab

        y, m, d = _to_iso_gdate(r["gregorian"]).split("-")
        dt = f"{y}{m}{d}"
        summary = first_label
        desc = f"Hijri: {r['hijri']} ({r['h_month_en']})\\nSemua label: {all_labels}"
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
    import pandas as pd
    from datetime import datetime, date
    
    st.header("📅 Kalender Islam")

    # ===== Hari ini =====
    today_display = datetime.now().strftime("%Y-%m-%d")
    st.write(f"Hari ini (Masehi): `{today_display}`")

    today_for_api = datetime.now().strftime("%d-%m-%Y")
    hijri = g_to_h(today_for_api)
    if not hijri:
        st.error("Tidak bisa mendapatkan konversi Hijriah dari API.")
        return

    try:
        h_month_num = int(hijri["month"]["number"])
        h_month_en  = hijri["month"]["en"]
        h_weekday_ar = hijri["weekday"]["ar"]
        h_date_str  = hijri["date"]
        h_year      = int(hijri["year"])
    except Exception as e:
        st.error(f"Format data Hijriah tak terduga: {e}")
        return

    st.success(f"Hari ini (Hijri): **{h_weekday_ar}, {h_date_str} {h_month_en} H**")

    st.subheader("⚙️ Pengaturan Tampilan")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        year_h = st.number_input("Tahun Hijriah", value=h_year, step=1,
                                 min_value=h_year - 3, max_value=h_year + 3)
    with c2:
        include_mon_thu = st.toggle("Tandai puasa Senin & Kamis", value=True)
    with c3:
        include_tasua   = st.toggle("Tandai Tāsū‘ā (9 Muharram)", value=True)
    with c4:
        only_labeled    = st.checkbox("Tampilkan hanya hari bertanda (event/puasa)", value=False)

    st.subheader("🗓️ Kalender")
    vm1, _ = st.columns([1, 3])
    options_vals = list(range(1, 13))
    default_idx  = max(min(h_month_num, 12), 1) - 1
    with vm1:
        view_month = st.selectbox(
            "Tampilan bulan (opsional)",
            options=options_vals,
            format_func=lambda x: f"Bulan {x}",
            index=default_idx,
            help="Pilih salah satu bulan Hijriah."
        )

    # ===== Helpers =====
    def _to_iso(s: str):
        s = str(s)
        if len(s) == 10 and s[2] == "-" and s[5] == "-":  # DD-MM-YYYY -> YYYY-MM-DD
            dd, mm, yyyy = s.split("-")
            return f"{yyyy}-{mm}-{dd}"
        return s

    def _parse_hijri_day(hijri_str: str):
        try:
            return int(str(hijri_str).split("-")[0])  # DD
        except Exception:
            return None

    def add_event_labels(df_in: pd.DataFrame, mark_mk: bool, mark_tasua: bool) -> pd.DataFrame:
        if df_in is None or df_in.empty:
            return df_in
        df2 = df_in.copy()
        out = []
        for _, r in df2.iterrows():
            tags = []
            if mark_mk:
                wd = str(r.get("weekday", "")).strip()
                if wd == "Monday":   tags.append("Puasa Senin")
                if wd == "Thursday": tags.append("Puasa Kamis")
            if mark_tasua:
                dnum = _parse_hijri_day(r.get("hijri", ""))
                hme  = str(r.get("h_month_en", "")).lower()
                if dnum == 9 and hme == "muharram":
                    tags.append("Tasū‘a (9 Muharram)")
            out.append(tags)  # <-- LIST, bukan string
        df2["labels"] = out
        return df2

    def _to_iso(s: str) -> str:
        s = str(s)
        # "DD-MM-YYYY" -> "YYYY-MM-DD"
        if len(s) == 10 and s[2] == "-" and s[5] == "-":
            dd, mm, yyyy = s.split("-")
            if len(yyyy) == 4:
                return f"{yyyy}-{mm}-{dd}"
        return s
    
    rows_all = []

    def _to_iso(s: str) -> str:
        s = str(s)
        # "DD-MM-YYYY" -> "YYYY-MM-DD"
        if len(s) == 10 and s[2] == "-" and s[5] == "-":
            dd, mm, yyyy = s.split("-")
            if len(yyyy) == 4:
                return f"{yyyy}-{mm}-{dd}"
        return s
    
    rows_all = []
    for m in range(1, 13):
        cal = h_to_g_calendar(int(year_h), m) or []
        for it in cal:
            g = it.get("gregorian", {})
            h = it.get("hijri", {})
            rows_all.append({
                "gregorian": g.get("date", ""),                       # "DD-MM-YYYY"
                "weekday":   g.get("weekday", {}).get("en", ""),
                "hijri":     h.get("date", ""),                       # "DD-MM-YYYY"
                "h_month_en":h.get("month", {}).get("en", ""),
                "h_month_num": h.get("month", {}).get("number", None),
                "labels":    "",
            })

    import pandas as pd
    from datetime import date
    
    rows_df = pd.DataFrame(rows_all)
    rows_df["gregorian"] = rows_df["gregorian"].apply(_to_iso)
    
    # backup kalau h_month_num belum ada
    if "h_month_num" not in rows_df.columns or rows_df["h_month_num"].isna().any():
        rows_df["h_month_num"] = rows_df["hijri"].astype(str).str.split("-").str[1].astype("Int64")
    
    # sort by date (robust utk find_upcoming)
    rows_df["__dt"] = pd.to_datetime(rows_df["gregorian"], errors="coerce")
    rows_df = rows_df.sort_values("__dt").drop(columns="__dt")
    
    # labelkan (Senin/Kamis, Tasū‘a)
    rows_df = add_event_labels(rows_df, include_mon_thu, include_tasua)
    rows_labeled = rows_df.to_dict("records")

    try:
        filtered  # noqa: F821
    except NameError:
        filtered = filter_rows(
            rows_labeled,           # dataset setahun yang sudah berlabel
            only_labeled=only_labeled,
            month_filter=view_month  # dari selectbox "Bulan ..."
        )

    if not filtered:
        if only_labeled:
            st.info("Tidak ada hari bertanda di bulan ini.")
        else:
            month_len = 30
            mm = int(view_month)
            yyyy = int(year_h)
            skeleton = []
            for d in range(1, month_len + 1):
                dd = f"{d:02d}"
                payload = h_to_g_single(f"{dd}-{mm:02d}-{yyyy}")
                if payload:
                    g = payload.get("gregorian", {}); h = payload.get("hijri", {})
                    skeleton.append({
                        "gregorian": _to_iso(g.get("date", "—")),                  # YYYY-MM-DD
                        "weekday":   g.get("weekday", {}).get("en", ""),
                        "hijri":     h.get("date", f"{dd}-{mm:02d}-{yyyy} H"),     # DD-MM-YYYY
                        "h_month_en":h.get("month", {}).get("en", ""),
                        "h_month_num": mm,                                         # penting utk filter_rows
                        "labels":    [],                                            # list, bukan string
                    })
                else:
                    skeleton.append({
                        "gregorian": "—",
                        "weekday": "",
                        "hijri": f"{dd}-{mm:02d}-{yyyy} H",
                        "h_month_en": "",
                        "h_month_num": mm,
                        "labels": [],
                    })
            filtered = skeleton

    # ===== Render tabel =====
    df = pd.DataFrame(
        filtered,
        columns=["gregorian", "weekday", "hijri", "h_month_en", "h_month_num", "labels"]
    )
    df = add_event_labels(df, include_mon_thu, include_tasua)
    
    # filter "hanya bertanda" (labels = list)
    if only_labeled:
        df = df[df["labels"].apply(lambda v: isinstance(v, list) and len(v) > 0)]
    
    # UI: tampilkan labels sebagai string
    def _labels_to_str(v):
        return ", ".join(v) if isinstance(v, list) else (v or "")
    
    df_tbl = df.copy()
    df_tbl["labels"] = df_tbl["labels"].apply(_labels_to_str)
    
    st.dataframe(
        df_tbl[["gregorian", "weekday", "hijri", "h_month_en", "labels"]],
        use_container_width=True, height=420
    )

    # ===== Unduhan =====
    export_rows = []
    for r in df.to_dict("records"):
        rr = r.copy()
        rr["labels"] = _labels_to_str(rr.get("labels"))
        export_rows.append(rr)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Unduh CSV Kalender (sesuai tampilan)",
            data=to_csv_bytes(export_rows),
            file_name=f"kalender_hijriah_{year_h}_bulan{view_month}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "📥 Ekspor .ICS (Google/Apple/Outlook)",
            data=to_ics_bytes(export_rows),
            file_name=f"kalender_hijriah_{year_h}_bulan{view_month}.ics",
            mime="text/calendar",
            use_container_width=True
        )

    st.caption("Catatan: kalender berdasar perhitungan (Umm al-Qura) – bisa bergeser ±1 hari dari rukyat lokal.")
