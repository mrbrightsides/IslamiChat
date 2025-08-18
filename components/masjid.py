import time
import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Mirror yang relatif stabil terlebih dahulu
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

def _run_overpass(endpoint: str, q: str):
    """Selalu GET untuk menghindari 400/CSRF pada beberapa mirror."""
    return requests.get(
        endpoint,
        params={"data": q},
        headers={"User-Agent": "IslamiChat/1.0"},
        timeout=(6, 14),  # (connect, read)
    )

def build_query(lat: float, lon: float, radius: int, lite: bool) -> str:
    if lite:
        return f"""
        [out:json][timeout:15];
        (
          node["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
          node["amenity"="place_of_worship"]["name"~"(?i)masjid|mushol+a|musala|surau"](around:{radius},{lat},{lon});
        );
        out center;
        """
    return f"""
    [out:json][timeout:20];
    (
      node["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
      way["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
      relation["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
      node["amenity"="place_of_worship"]["name"~"(?i)masjid|mushol+a|musala|surau"](around:{radius},{lat},{lon});
      way["amenity"="place_of_worship"]["name"~"(?i)masjid|mushol+a|musala|surau"](around:{radius},{lat},{lon});
      relation["amenity"="place_of_worship"]["name"~"(?i)masjid|mushol+a|musala|surau"](around:{radius},{lat},{lon});
    );
    out center;
    """

@st.cache_data(ttl=300)
def fetch_mosques(lat: float, lon: float, radius: int, lite: bool):
    q = build_query(lat, lon, radius, lite)
    last_err = []
    for ep in OVERPASS_ENDPOINTS:
        delay = 1.2
        for attempt in range(2):  # fail-fast
            try:
                resp = _run_overpass(ep, q)
                if resp.status_code == 429:
                    time.sleep(delay); delay *= 1.6
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data.get("elements", [])
            except Exception as e:
                last_err.append(f"{ep} try{attempt+1}: {e}")
                time.sleep(delay); delay *= 1.6
    raise RuntimeError("Overpass gagal: " + " | ".join(last_err[:3]) + " …")

# ---------- Lokasi ----------
@st.cache_data(ttl=600)
def ip_lookup():
    r = requests.get("https://ipinfo.io/json", timeout=8, headers={"User-Agent": "IslamiChat/1.0"})
    r.raise_for_status()
    loc = (r.json().get("loc") or "").split(",")
    if len(loc) == 2:
        return float(loc[0]), float(loc[1])
    raise ValueError("Tidak ada koordinat pada respons IP")

@st.cache_data(ttl=86400)
def geocode_place(q: str):
    geo = Nominatim(user_agent="islamiChat/1.0", timeout=10)
    loc = geo.geocode(q, language="id")
    if not loc:
        return None
    return float(loc.latitude), float(loc.longitude), loc.address

def get_user_location():
    try:
        return ip_lookup()
    except Exception:
        return None, None

def show_nearby_mosques():
    st.header("🕌 Masjid Terdekat")

    col1, col2 = st.columns([2, 1])
    with col1:
        use_ip = st.toggle("Gunakan lokasi berdasarkan IP", value=True,
                           help="Jika dimatikan, tulis nama lokasi secara manual di bawah.")
    with col2:
        radius = st.slider("Radius pencarian (meter)", 300, 4000, 1500, step=100)
    lite = st.toggle("Gunakan query ringan (lebih mudah lolos rate-limit)", value=True)

    lat, lon, label = None, None, ""

    if use_ip:
        try:
            lat, lon = ip_lookup()
            label = "Lokasi berdasarkan IP"
        except Exception as e:
            st.warning(f"Gagal dapat lokasi IP: {e}")
    else:
        q = st.text_input("Masukkan nama lokasi (contoh: Palembang, Indonesia)", value="Palembang, Indonesia")
        if q.strip():
            g = geocode_place(q.strip())
            if g:
                lat, lon, label = g
            else:
                st.error("Lokasi tidak ditemukan. Coba lebih spesifik.")
                return
        else:
            st.info("Masukkan nama lokasi terlebih dahulu.")
            return

    if lat is None or lon is None:
        st.warning("Tidak dapat menentukan koordinat lokasi.")
        return

    try:
        elements = fetch_mosques(lat, lon, radius, lite)
    except Exception as e:
        st.error(f"Gagal mengambil data masjid terdekat: {e}")
        st.caption("Coba kecilkan radius, aktifkan 'Lite query', lalu klik Rerun.")
        return

    m = folium.Map(location=[lat, lon], zoom_start=14, control_scale=True)
    folium.Marker([lat, lon], tooltip=label or "Lokasi Anda",
                  icon=folium.Icon(color="blue", icon="user")).add_to(m)

    cluster = MarkerCluster(name="Masjid").add_to(m)
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or "Masjid"
        lat_m = el.get("lat") or el.get("center", {}).get("lat")
        lon_m = el.get("lon") or el.get("center", {}).get("lon")
        if lat_m and lon_m:
            folium.Marker([lat_m, lon_m],
                          tooltip=name,
                          popup=folium.Popup(name, max_width=300),
                          icon=folium.Icon(color="green", icon="info-sign")).add_to(cluster)
            count += 1

    st.success(f"Ditemukan {count} lokasi dalam radius {radius} m.")
    st_folium(m, width=800, height=520)
