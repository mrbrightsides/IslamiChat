import time
import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

def _run_overpass(endpoint: str, q: str):
    return requests.post(
        endpoint, data={"data": q},
        headers={"User-Agent": "IslamiChat/1.0"},
        timeout=(6, 20)
    )

def build_query(lat: float, lon: float, radius: int, lite: bool) -> str:
    name_regex = "masjid|musholl?a|mushol?a|mus(ha)?ll?a|musala|surau|langgar|prayer.?room"
    if lite:
        return f"""
        [out:json][timeout:20];
        (
          node["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
          node["amenity"="place_of_worship"]["name"~"{name_regex}", i](around:{radius},{lat},{lon});
          node["building"="mosque"](around:{radius},{lat},{lon});
        );
        out center;
        """
    return f"""
    [out:json][timeout:25];
    (
      node["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
      way["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});
      relation["amenity"="place_of_worship"]["religion"="muslim"](around:{radius},{lat},{lon});

      node["amenity"="place_of_worship"]["name"~"{name_regex}", i](around:{radius},{lat},{lon});
      way["amenity"="place_of_worship"]["name"~"{name_regex}", i](around:{radius},{lat},{lon});
      relation["amenity"="place_of_worship"]["name"~"{name_regex}", i](around:{radius},{lat},{lon});

      node["building"="mosque"](around:{radius},{lat},{lon});
      way["building"="mosque"](around:{radius},{lat},{lon});
    );
    out center;
    """

@st.cache_data(ttl=300)
def fetch_mosques(lat: float, lon: float, radius: int, lite: bool):
    q = build_query(lat, lon, radius, lite)
    last_err = []
    for ep in OVERPASS_ENDPOINTS:
        delay = 1.2
        for attempt in range(2):
            try:
                r = _run_overpass(ep, q)
                if r.status_code == 429:
                    time.sleep(delay); delay *= 1.6; continue
                r.raise_for_status()
                return r.json().get("elements", [])
            except Exception as e:
                last_err.append(f"{ep} try{attempt+1}: {e}")
                time.sleep(delay); delay *= 1.6
    raise RuntimeError("Overpass gagal: " + " | ".join(last_err[:3]) + " …")

@st.cache_data(ttl=86400)
def geocode_place(q: str):
    geo = Nominatim(user_agent="islamiChat/1.0", timeout=10)
    loc = geo.geocode(q, language="id")
    if not loc: return None
    return float(loc.latitude), float(loc.longitude), loc.address

def show_nearby_mosques():
    st.header("🕌 Masjid Terdekat")

    col_r, = st.columns(1)
    radius = col_r.slider("Radius pencarian (meter)", 300, 4000, 1500, step=100)

    lite = st.toggle("Gunakan query ringan (lebih mudah lolos rate-limit)", value=False)

    q = st.text_input("Masukkan nama lokasi (contoh: Palembang, Indonesia)", value="Palembang, Indonesia")
    if not q.strip():
        st.info("Masukkan lokasi terlebih dahulu."); return

    g = geocode_place(q.strip())
    if not g:
        st.error("Lokasi tidak ditemukan. Coba lebih spesifik."); return
    lat, lon, label = g
    st.caption(f"Lokasi dicari pada: {label}  •  ({lat:.5f}, {lon:.5f})")

    try:
        elements = fetch_mosques(lat, lon, radius, lite)
        if not elements:
            new_radius = min(max(2*radius, 1000), 4000)
            st.info(f"Belum ada hasil. Mencoba ulang radius {new_radius} m & query lengkap…")
            elements = fetch_mosques(lat, lon, new_radius, False)
            radius = new_radius
    except Exception as e:
        st.error(f"Gagal mengambil data masjid: {e}")
        return

    m = folium.Map(location=[lat, lon], zoom_start=13, control_scale=True)
    folium.Marker([lat, lon], tooltip=label, icon=folium.Icon(color="blue", icon="user")).add_to(m)
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
    try:
        st_folium(m, width=800, height=520)
    except Exception as e:
        st.warning("Map gagal dimuat. Coba reload halaman."); st.caption(str(e))
