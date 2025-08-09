import time
import requests
import datetime as dt
import pytz
import streamlit as st
from streamlit.components.v1 import html

# ====== Page setup ======
st.set_page_config(page_title="IslamiChat 🤖", layout="wide")
st.title("IslamiChat = Tanya Jawab + Waktu Sholat")
st.caption("Powered by ArtiBot / Botsonic • Waktu sholat dari Aladhan API")

tab_chat, tab_prayer = st.tabs(["🤖 Chatbot", "🕋 Waktu Sholat"])

# ====== TAB 1: Chatbot ======
with tab_chat:
    st.subheader("Pilih widget:")
    widget_opt = st.radio(
        " ", 
        ["ArtiBot", "BotSonic", "TawkTo"], 
        horizontal=True, label_visibility="collapsed"
    )

    container_css = """
    <div style="display:flex;justify-content:center;width:100%;">
      <div style="width:90%;max-width:1200px;">
        {WIDGET}
      </div>
    </div>
    """

    ARTIBOT = """
    <script type="text/javascript">
    !function(t,e){t.artibotApi={l:[],t:[],on:function(){this.l.push(arguments)},trigger:function(){this.t.push(arguments)}};
    var a=!1,i=e.createElement("script");i.async=!0,i.type="text/javascript",i.src="https://app.artibot.ai/loader.js",
    e.getElementsByTagName("head").item(0).appendChild(i),
    i.onreadystatechange=i.onload=function(){if(!(a||this.readyState&&"loaded"!=this.readyState&&"complete"!=this.readyState)){
      new window.ArtiBot({i:"5ace9d64-708e-48cb-86df-b8c605d17c1e"});a=!0}}}(window,document);
    </script>
    """

    BOTSONIC = """
    <iframe style="height:85vh;width:100%;border:0;border-radius:12px" frameBorder="0" 
      src="https://widget.botsonic.com/CDN/index.html?service-base-url=https%3A%2F%2Fapi-bot.writesonic.com&token=78d9eaba-80fc-4293-b290-fe72e1899607&base-origin=https%3A%2F%2Fbot.writesonic.com&instance-name=Botsonic&standalone=true&page-url=https%3A%2F%2Fislamichat.streamlit.app%2Fbots%2Fa148b878-259e-4591-858a-8869b9b23604%2Fconnect">
    </iframe>
    """

    # ganti URL di bawah dengan Space kamu sendiri
    TAWKTO = """
<script type="text/javascript">
var Tawk_API=Tawk_API||{}, Tawk_LoadStart=new Date();
(function(){
var s1=document.createElement("script"),s0=document.getElementsByTagName("script")[0];
s1.async=true;
s1.src='https://embed.tawk.to/63f1709c4247f20fefe15b12/1gpjhvpnb';
s1.charset='UTF-8';
s1.setAttribute('crossorigin','*');
s0.parentNode.insertBefore(s1,s0);
})();
</script>
    """

    html_map = {
        "ArtiBot": ARTIBOT,
        "BotSonic": BOTSONIC,
        "TawkTo": TAWKTO
    }

    html(container_css.replace("{WIDGET}", html_map[widget_opt]), height=750)
    
# ====== Helpers untuk Waktu Sholat ======
TZ = pytz.timezone("Asia/Jakarta")
METHODS = {
    "UOIF (Europe)": 12,
    "Moonsighting Committee": 20,
    "ISNA (North America)": 2,
    "Umm Al-Qura, Makkah": 4,
    "Egyptian General Authority": 5,
    "Kemenag RI (pakai Moonsighting proxy)": 20,
}

@st.cache_data(show_spinner=False, ttl=300)
def fetch_timings_by_city(city: str, country: str, method: int):
    url = "https://api.aladhan.com/v1/timingsByCity"
    r = requests.get(
        url,
        params={"city": city, "country": country, "method": method, "school": 0},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError(data)
    return data["data"]  # contains date + timings

def parse_today_times(timings_dict):
    keys = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    return {k: timings_dict[k] for k in keys if k in timings_dict}

def to_local_datetime(date_readable: str, time_str: str):
    # date_readable: "09 Aug 2025"
    d = dt.datetime.strptime(date_readable, "%d %b %Y").date()
    hh, mm = [int(x) for x in time_str.split(":")[:2]]
    naive = dt.datetime(d.year, d.month, d.day, hh, mm)
    return TZ.localize(naive)

def next_prayer(now_local: dt.datetime, times_local: dict):
    upcoming = [(name, t) for name, t in times_local.items() if t > now_local]
    if upcoming:
        return sorted(upcoming, key=lambda x: x[1])[0]
    return None, None

def fmt_delta(delta: dt.timedelta):
    s = int(delta.total_seconds()); s = max(s, 0)
    h = s // 3600; m = (s % 3600) // 60; ss = s % 60
    parts = []
    if h: parts.append(f"{h} jam")
    if m or (h and ss): parts.append(f"{m} mnt")
    if h == 0: parts.append(f"{ss} dtk")
    return " ".join(parts)

# ====== TAB 2: Waktu Sholat ======
with tab_prayer:
    st.subheader("Waktu Sholat Harian")
    c1, c2, c3 = st.columns([2,2,2])
    with c1:
        city = st.text_input("Kota", value="Palembang")
    with c2:
        country = st.text_input("Negara", value="Indonesia")
    with c3:
        method_name = st.selectbox("Metode perhitungan", list(METHODS.keys()), index=1)
    method = METHODS[method_name]

    try:
        payload = fetch_timings_by_city(city, country, method)
        date_readable = payload["date"]["readable"]
        timings = parse_today_times(payload["timings"])
        times_local = {n: to_local_datetime(date_readable, t.split(" ")[0]) for n, t in timings.items()}

        st.write(f"📅 **{date_readable}** — Zona: **{TZ.zone}** — Metode: **{method_name}**")

        rows = [(n, timings[n]) for n in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"] if n in timings]
        st.table(rows)

        # Countdown sekali tampil (tanpa loop agar ringan). Klik Rerun untuk refresh manual.
        now = dt.datetime.now(TZ)
        name, tnext = next_prayer(now, times_local)
        if name:
            st.success(f"Sholat berikutnya: **{name}** — **{tnext.strftime('%H:%M')}** (≈ {fmt_delta(tnext - now)})")
            st.caption("Hitung mundur diperbarui saat halaman di-run ulang. (Gunakan tombol Rerun di atas jika perlu.)")
        else:
            st.info("Semua waktu sholat hari ini sudah lewat. Lihat Fajr esok hari.")
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
        st.caption("Coba ganti metode / periksa koneksi.")
