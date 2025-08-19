import math
import streamlit as st
from streamlit.components.v1 import html

# --- opsional: import folium hanya saat diperlukan ---
def _lazy_import_folium():
    import importlib
    return importlib.import_module("folium")

# ============== UTIL ==============
def _bearing_gc(lat, lon, lat2=21.422487, lon2=39.826206):
    import math
    φ1, φ2 = math.radians(lat), math.radians(lat2)
    Δλ = math.radians(lon2 - lon)
    y = math.sin(Δλ) * math.cos(φ2)
    x = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def _haversine_km(lat, lon, lat2=21.422487, lon2=39.826206):
    R = 6371.0088
    import math
    φ1, φ2 = math.radians(lat), math.radians(lat2)
    dφ = math.radians(lat2 - lat)
    dλ = math.radians(lon2 - lon)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2*R*math.asin(math.sqrt(a))

@st.cache_data(show_spinner=False)
def _cached_map_html(lat, lon, bearing, zoom=6):
    """Bangun HTML peta satu kali per kombinasi parameter."""
    folium = _lazy_import_folium()
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles="CartoDB positron")
    folium.Marker([lat, lon], tooltip="Lokasi Anda").add_to(m)
    folium.Marker([21.422487, 39.826206], tooltip="Ka'bah",
                  icon=folium.Icon(color="green", icon="star")).add_to(m)
    folium.PolyLine([[lat, lon], [21.422487, 39.826206]],
                    tooltip=f"Garis Kiblat {bearing:.2f}°").add_to(m)
    return m._repr_html_()

def _map_html(lat, lon, bearing):
    m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB positron")
    folium.Marker([lat, lon], tooltip="Lokasi Anda").add_to(m)
    folium.Marker([KAABA_LAT, KAABA_LON], tooltip="Ka'bah (Masjidil Haram)",
                  icon=folium.Icon(color="green", icon="star")).add_to(m)
    folium.PolyLine([[lat, lon], [KAABA_LAT, KAABA_LON]],
                    tooltip=f"Garis Kiblat {bearing:.2f}°").add_to(m)
    return m._repr_html_()

def _compass_html(qibla_deg: float) -> str:
    # Pakai placeholder __QIBLA__ lalu replace -> aman dari kurung kurawal CSS/JS
    html_str = """
    <style>
      .compass-wrap {
        display:flex; align-items:center; justify-content:center;
        height:180px; margin:8px 0 4px 0;
      }
      .dial { width:140px; height:140px; border:2px solid #444; border-radius:50%;
              position:relative; background:radial-gradient(#111, #222); }
      .tick { position:absolute; left:50%; top:2px; width:2px; height:10px; background:#777; transform-origin:50% 68px; }
      .north { position:absolute; top:6px; left:50%; transform:translateX(-50%); color:#bbb; font-size:12px; }
      .arrow {
        position:absolute; left:50%; top:50%;
        width:0; height:0; transform-origin:50% 60px;
        border-left:10px solid transparent; border-right:10px solid transparent;
        border-bottom:50px solid #5cff8d;
        filter: drop-shadow(0 0 6px rgba(92,255,141,.25));
      }
      .legend { text-align:center; color:#bbb; font-size:0.9rem; }
      .perm-btn {
        display:inline-block; padding:6px 10px; border:1px solid #666; border-radius:6px; cursor:pointer; margin-top:6px; color:#ddd;
      }
    </style>
    <div class="compass-wrap">
      <div class="dial" id="dial">
        <div class="north">N</div>
        <div class="tick" style="transform:rotate(0deg) translateX(-1px);"></div>
        <div class="tick" style="transform:rotate(90deg) translateX(-1px);"></div>
        <div class="tick" style="transform:rotate(180deg) translateX(-1px);"></div>
        <div class="tick" style="transform:rotate(270deg) translateX(-1px);"></div>
        <div class="arrow" id="arrow"></div>
      </div>
    </div>
    <div class="legend">
      <div>Putar perangkat hingga panah <b>menghadap ke atas</b> (arah N) — itu arah kiblat.</div>
      <div id="readout" style="margin-top:6px; font-family:monospace;"></div>
      <div id="perm" style="margin-top:8px; display:none">
        <span class="perm-btn" onclick="reqPerm()">Aktifkan sensor (iOS)</span>
      </div>
    </div>

    <script>
      const QIBLA = __QIBLA__;  // derajat dari utara, searah jarum jam
      const arrow = document.getElementById('arrow');
      const readout = document.getElementById('readout');
      const permBox = document.getElementById('perm');

      function updateArrow(heading){
        // heading: 0=N, searah jarum jam
        const delta = ((QIBLA - heading) % 360 + 360) % 360;
        // hindari template literal biar aman dari f-string: pakai concatenation
        arrow.style.transform = 'translate(-50%, -60px) rotate(' + delta + 'deg)';
        readout.textContent = 'Heading: ' + heading.toFixed(1) + '°  |  Kiblat: ' +
                              QIBLA.toFixed(2) + '°  |  Delta: ' + delta.toFixed(1) + '°';
      }

      function onOrient(e){
        let heading = null;
        if (e.webkitCompassHeading !== undefined) {
          heading = e.webkitCompassHeading;
        } else if (e.absolute === true && e.alpha !== null) {
          heading = 360 - e.alpha;
        }
        if (heading !== null) updateArrow((heading%360+360)%360);
      }

      function start(){
        if (typeof DeviceOrientationEvent !== 'undefined' &&
            typeof DeviceOrientationEvent.requestPermission === 'function') {
          permBox.style.display = 'block';
        } else {
          window.addEventListener('deviceorientation', onOrient, true);
        }
      }

      function reqPerm(){
        DeviceOrientationEvent.requestPermission().then(state => {
          if (state === 'granted') {
            window.addEventListener('deviceorientation', onOrient, true);
            permBox.style.display = 'none';
          }
        }).catch(console.warn);
      }

      start();
    </script>
    """
    return html_str.replace("__QIBLA__", f"{qibla_deg:.6f}")

from streamlit_js_eval import get_geolocation

def use_my_location(lat_default: float, lon_default: float):
    if "geo_clicks" not in st.session_state:
        st.session_state.geo_clicks = 0

    colA, colB = st.columns([1, 3])
    with colA:
        if st.button("📍 Gunakan Lokasi Saya", use_container_width=True):
            st.session_state.geo_clicks += 1
    with colB:
        st.caption("Jika diminta, izinkan akses lokasi pada browser (HTTPS wajib).")

    lat, lon, updated = lat_default, lon_default, False

    if st.session_state.geo_clicks > 0:
        with st.spinner("Mengambil lokasi dari browser…"):
            loc = get_geolocation()   # tanpa argumen

        if isinstance(loc, dict):
            if "coords" in loc and isinstance(loc["coords"], dict):
                c = loc["coords"]
                if "latitude" in c and "longitude" in c:
                    lat, lon = float(c["latitude"]), float(c["longitude"])
                    updated = True
            elif "latitude" in loc and "longitude" in loc:
                lat, lon = float(loc["latitude"]), float(loc["longitude"])
                updated = True

        if updated:
            st.success("Lokasi berhasil diambil dari GPS ✅")
        else:
            st.info("Belum menerima koordinat. Coba klik tombolnya lagi atau cek izin lokasi.")

    return lat, lon, updated

def show_kiblat_tab_plus():
    st.title("🧭 Arah Kiblat (Peta + Kompas)")
    st.caption("Kompas realtime + mode manual. Peta dibangun saat diminta agar ringan.")

    # --- init state ---
    if "lat" not in st.session_state: st.session_state.lat = -2.990934
    if "lon" not in st.session_state: st.session_state.lon = 104.756554
    if "lat_input" not in st.session_state: st.session_state.lat_input = float(st.session_state.lat)
    if "lon_input" not in st.session_state: st.session_state.lon_input = float(st.session_state.lon)

    # --- input ringan ---
    c1, c2 = st.columns(2)
    with c1: st.session_state.lat_input = st.number_input("Latitude", value=float(st.session_state.lat_input))
    with c2: st.session_state.lon_input = st.number_input("Longitude", value=float(st.session_state.lon_input))
    st.session_state.lat = float(st.session_state.lat_input)
    st.session_state.lon = float(st.session_state.lon_input)

    # --- tombol GPS (panggil SEKALI) ---
    lat_new, lon_new, updated = use_my_location(st.session_state.lat, st.session_state.lon)
    if updated:
        st.session_state.lat = lat_new; st.session_state.lon = lon_new
        st.session_state.lat_input = float(lat_new); st.session_state.lon_input = float(lon_new)
        st.toast("Lokasi ter-update dari GPS", icon="📍")
        st.rerun()  # rerun sekali saja saat GPS sukses

    # --- hitung bearing/jarak (cepat) ---
    lat, lon = st.session_state.lat, st.session_state.lon
    bearing = _bearing_gc(lat, lon)
    dist_km = _haversine_km(lat, lon)
    st.success(f"Arah Kiblat: **{bearing:.2f}°** dari utara. Jarak ke Ka'bah: **{dist_km:,.0f} km**.")

    # --- kompas realtime (ringan) ---
    st.markdown("#### 📳 Kompas Realtime")
    html(_compass_html(bearing), height=260)

    # --- peta: TUNDA render sampai user minta ---
    show_map = st.toggle("🗺️ Tampilkan peta garis ke Ka'bah", value=False)
    if show_map:
        zoom = st.slider("Zoom peta", 4, 12, 6, 1)
        with st.spinner("Membangun peta…"):
            map_html = _cached_map_html(lat, lon, bearing, zoom=zoom)
        html(map_html, height=420, scrolling=False)

    # --- mode manual (tetap ringan) ---
    st.markdown("#### 🧭 Mode Manual (tanpa sensor)")
    heading_manual = st.slider("Heading saya (0°=Utara, 90°=Timur, 180°=Selatan, 270°=Barat)", 0, 359, 0, 1)
    delta = (bearing - heading_manual) % 360
    a, b = st.columns([1,2])
    with a: html(_manual_compass_html(delta), height=200)
    with b:
        st.info(
            f"Arah Kiblat relatif ke Utara: **{bearing:.2f}°**.\n\n"
            f"Heading kamu sekarang: **{heading_manual}°** → "
            f"putar badan sampai panah ke **{delta:.1f}°** dari Utara."
        )

def _manual_compass_html(delta_deg: float) -> str:
    # delta_deg = berapa derajat dari UTARA yang harus dihadapkan (0..360)
    html_str = """
    <style>
      .dial { width:140px; height:140px; border:2px solid #444; border-radius:50%;
              position:relative; background:radial-gradient(#111, #222); margin:auto; }
      .north { position:absolute; top:6px; left:50%; transform:translateX(-50%); color:#bbb; font-size:12px; }
      .arrow {
        position:absolute; left:50%; top:50%;
        width:0; height:0; transform-origin:50% 60px;
        border-left:10px solid transparent; border-right:10px solid transparent;
        border-bottom:50px solid #5cff8d; filter: drop-shadow(0 0 6px rgba(92,255,141,.25));
      }
    </style>
    <div class="dial">
      <div class="north">N</div>
      <div class="arrow" style="transform: translate(-50%, -60px) rotate(__DELTA__deg);"></div>
    </div>
    <div style="text-align:center;color:#bbb;margin-top:6px;font-size:0.9rem;">
      Arahkan ponsel sehingga panah menghadap ke atas (N). Itu arah kiblat.
    </div>
    """
    return html_str.replace("__DELTA__", f"{delta_deg:.1f}")

