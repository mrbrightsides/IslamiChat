import math
import streamlit as st
import folium
from streamlit.components.v1 import html
from streamlit_js_eval import get_geolocation

_HAS_GEOLOC = False
try:
    from streamlit_geolocation import geolocation as _geolocation
    _HAS_GEOLOC = True
except Exception:
    try:
        from streamlit_js_eval import get_geolocation as _get_geolocation
        _HAS_GEOLOC = True
    except Exception:
        _HAS_GEOLOC = False

KAABA_LAT = 21.422487
KAABA_LON = 39.826206

def _bearing_gc(lat1, lon1, lat2=KAABA_LAT, lon2=KAABA_LON):
    """Great-circle initial bearing (deg) from (lat1,lon1) to (lat2,lon2)."""
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δλ = math.radians(lon2 - lon1)
    y = math.sin(Δλ) * math.cos(φ2)
    x = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    return brng

def _haversine_km(lat1, lon1, lat2=KAABA_LAT, lon2=KAABA_LON):
    R = 6371.0088
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return 2*R*math.asin(math.sqrt(a))

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

def use_my_location(lat_default: float, lon_default: float):
    """
    Klik tombol -> minta izin -> jika browser mengembalikan koordinat,
    return lat/lon baru. Jika None, jangan tulis 'gagal'—minta user klik lagi.
    """
    colA, colB = st.columns([1, 3])
    with colA:
        clicked = st.button("📍 Gunakan Lokasi Saya", use_container_width=True)
    with colB:
        st.caption("Jika diminta, izinkan akses lokasi pada browser.")

    lat, lon = lat_default, lon_default
    if not clicked:
        return lat, lon, False  # False = belum update

    with st.spinner("Mengambil lokasi dari browser…"):
        loc = get_geolocation()  # bisa balik None dulu
    if isinstance(loc, dict) and "latitude" in loc and "longitude" in loc:
        lat = float(loc["latitude"])
        lon = float(loc["longitude"])
        st.success("Lokasi berhasil diambil dari GPS.")
        return lat, lon, True

    # Tidak error—hanya info agar user coba lagi
    st.info("Belum menerima koordinat. Coba klik lagi atau cek izin lokasi (HTTPS wajib).")
    return lat, lon, False

def show_kiblat_tab_plus():
    st.title("🧭 Arah Kiblat (Peta + Kompas)")
    st.caption("Gunakan kompas realtime dan peta. Jika sensor tidak tersedia, pakai Mode Manual.")

    # Default contoh (mis. Palembang)
    default_lat, default_lon = -2.990934, 104.756554

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=default_lat, help="Contoh: Palembang ≈ -2.990934")
    with col2:
        lon = st.number_input("Longitude", value=default_lon, help="Contoh: Palembang ≈ 104.756554")

    # Tombol GPS → override lat/lon jika berhasil
    lat, lon = _use_my_location(lat, lon)

    # Hitung bearing & jarak seperti sebelumnya…
    bearing = _bearing_gc(lat, lon)
    dist_km = _haversine_km(lat, lon)

    st.success(f"Arah Kiblat: **{bearing:.2f}°** dari utara. Jarak ke Ka'bah: **{dist_km:,.0f} km**.")

    # Kompas realtime (HTML JS kamu yang sebelumnya)
    st.markdown("#### 📳 Kompas Realtime")
    html(_compass_html(bearing), height=260)

    # Peta (seperti sebelumnya)
    st.markdown("#### 🗺️ Peta Garis Kiblat")
    html(_map_html(lat, lon, bearing), height=420, scrolling=False)

    # Mode manual (fallback) — blok kamu yang sudah jalan tadi
    st.markdown("#### 🧭 Mode Manual (tanpa sensor)")
    st.caption("Kalau kompas di atas tidak bergerak (HP tidak mendukung sensor), gunakan mode manual ini.")
    heading_manual = st.slider(
        "Heading saya (0°=Utara, 90°=Timur, 180°=Selatan, 270°=Barat)",
        min_value=0, max_value=359, value=0, step=1
    )
    delta = (bearing - heading_manual) % 360
    colA, colB = st.columns([1,2])
    with colA:
        html(_manual_compass_html(delta), height=200)
    with colB:
        st.info(
            f"Arah Kiblat relatif ke Utara: **{bearing:.2f}°**.\n\n"
            f"Heading kamu sekarang: **{heading_manual}°** → "
            f"putar badan sampai panah ke **{delta:.1f}°** dari Utara (panah menghadap ke atas)."
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

