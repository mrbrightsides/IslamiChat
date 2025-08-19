# components/kiblat_plus.py
import math
import streamlit as st
import folium
from streamlit.components.v1 import html

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

def show_kiblat_tab_plus():
    st.title("🧭 Arah Kiblat (Peta + Kompas)")
    st.caption("Gunakan kompas di bawah (realtime) dan peta garis lurus ke Ka'bah. "
               "Catatan: kompas ponsel dipengaruhi **magnet** & **kalibrasi**; gunakan sebagai panduan, verifikasi jika perlu.")

    # Input lokasi (lat/lon). Kamu bisa ganti dengan geocoder yang kamu pakai sekarang.
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=-2.990934, help="Contoh: Palembang ≈ -2.990934")
    with col2:
        lon = st.number_input("Longitude", value=104.756554, help="Contoh: Palembang ≈ 104.756554")

    # Hitung bearing & jarak
    bearing = _bearing_gc(lat, lon)
    dist_km = _haversine_km(lat, lon)

    st.success(f"Arah Kiblat: **{bearing:.2f}°** dari utara (searah jarum jam). Jarak ke Ka'bah: **{dist_km:,.0f} km**.")

    # Kompas realtime
    st.markdown("#### 📳 Kompas Realtime")
    html(_compass_html(bearing), height=260)

    # Peta garis ke Ka'bah
    st.markdown("#### 🗺️ Peta Garis Kiblat")
    html(_map_html(lat, lon, bearing), height=420, scrolling=False)

    with st.expander("ℹ️ Tips akurasi & kalibrasi"):
        st.markdown(
            "- Jauhkan ponsel dari magnet/metal (earpods, casing magnet, motor).  \n"
            "- **Kalibrasi** kompas ponsel (gerakkan angka delapan/∞ selama 10–20 detik).  \n"
            "- Arahkan badan menghadap **panah** pada kompas hingga di atas huruf **N**.  \n"
            "- Di dalam gedung tinggi/keramaian elektromagnetik, gunakan **peta** sebagai konfirmasi."
        )
