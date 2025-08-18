import time
import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# ===== Overpass setup =====
OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

def _run_overpass(endpoint: str, q: str):
    return requests.post(
        endpoint,
        data={"data": q},
        headers={"User-Agent": "IslamiChat/1.0"},
        timeout=(6, 20),   # (connect, read)
    )

def build_query(lat: float, lon: float, radius: int, lite: bool) -> str:
    # regex nama masjid yg umum dipakai di Indonesia (case-insensitive pakai ", i")
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
        for attempt in range(2):  # fail-fast
            try:
                r = _run_overpass(ep, q)
                if r.status_code == 429:
                    time.sleep(delay); delay *= 1.6
                    continue
                r.raise_for_status()
                return r.json().get("elements", [])
            except Exception as e:
                last_err.append(f"{ep} try{attempt+1}: {e}")
                time.sleep(delay); delay *= 1.6
    raise RuntimeError("Overpass gagal: " + " | ".join(last_err[:3]) + " …")

# ===== Geocoding (multi-kandidat) =====
@st.cache_data(ttl=3600)
def geocode_candidates(q: str, country_bias: str | None = "id"):
    geo = Nominatim(user_agent="islamiChat/1.0", timeout=10)
    # exactly_one=False agar dapat beberapa kandidat
    results = geo.geocode(
        q, language="id", addressdetails=True, exactly_one=False,
        limit=5, country_codes=country_bias
    )
    if not results:
        return []
    out = []
    for r in results:
        out.append({"label": r.address, "lat": float(r.latitude), "lon": float(r.longitude)})
    return out

# ===== UI =====
def show_nearby_mosques():
    st.header("🕌 Masjid Terdekat")

    radius = st.slider("Radius pencarian (meter)", 300, 4000, 1500, step=100)
    lite = st.toggle("Gunakan query ringan (lebih mudah lolos rate-limit)", value=False)

    # input alamat bebas
    q = st.text_input(
        "Masukkan alamat/lokasi (contoh: Jl. Jendral Sudirman, 8 Ilir, Palembang)",
        value="Palembang, Indonesia"
    )

    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button("🔎 Cari alamat"):
            if q.strip():
                st.session_state["_cands"] = geocode_candidates(q.strip())
            else:
                st.warning("Tulis alamat atau nama lokasi terlebih dahulu.")

    cands = st.session_state.get("_cands", geocode_candidates(q))  # isi awal dari nilai default
    if not cands:
        st.error("Lokasi tidak ditemukan. Coba lebih spesifik.")
        return

    labels = [c["label"] for c in cands]
    idx = st.selectbox("Pilih lokasi yang sesuai:", range(len(cands)), format_func=lambda i: labels[i])
    lat, lon = cands[idx]["lat"], cands[idx]["lon"]
    st.caption(f"Lokasi dipilih: {labels[idx]} • ({lat:.5f}, {lon:.5f})")

    # ===== Ambil data masjid (+fallback kalau kosong) =====
    try:
        elements = fetch_mosques(lat, lon, radius, lite)
        if not elements:
            new_radius = min(max(2 * radius, 1000), 4000)
            st.info(f"Belum ada hasil. Mencoba ulang radius {new_radius} m & query lengkap…")
            elements = fetch_mosques(lat, lon, new_radius, False)
            radius = new_radius
    except Exception as e:
        st.error(f"Gagal mengambil data masjid: {e}")
        return

    # ===== Peta =====
    m = folium.Map(location=[lat, lon], zoom_start=14, control_scale=True)
    folium.Marker([lat, lon], tooltip="Titik pencarian",
                  icon=folium.Icon(color="blue", icon="user")).add_to(m)

    cluster = MarkerCluster(name="Masjid").add_to(m)
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or "Masjid"
        lat_m = el.get("lat") or el.get("center", {}).get("lat")
        lon_m = el.get("lon") or el.get("center", {}).get("lon")
        if lat_m and lon_m:
            folium.Marker(
                [lat_m, lon_m],
                tooltip=name,
                popup=folium.Popup(name, max_width=300),
                icon=folium.Icon(color="green", icon="info-sign"),
            ).add_to(cluster)
            count += 1

    st.success(f"Ditemukan {count} lokasi dalam radius {radius} m.")

    # render dan simpan state peta
    map_state = st_folium(m, width=800, height=520)

    # ===== Cari ulang dari center peta (opsional) =====
    with st.expander("🔁 Cari ulang dari titik tengah peta ini"):
        st.caption("Geser/zoom peta di atas, lalu klik tombol di bawah untuk mencari dari center tampilan.")
        if st.button("Cari dari center peta"):
            if map_state and "center" in map_state:
                cen_lat = map_state["center"]["lat"]
                cen_lon = map_state["center"]["lng"]
            elif map_state and "bounds" in map_state:
                # fallback hitung center dari bounds
                cen_lat = (map_state["bounds"]["_southWest"]["lat"] + map_state["bounds"]["_northEast"]["lat"]) / 2
                cen_lon = (map_state["bounds"]["_southWest"]["lng"] + map_state["bounds"]["_northEast"]["lng"]) / 2
            else:
                st.warning("Center peta belum terbaca. Coba gerakkan/zoom peta dulu.")
                st.stop()

            # simpan kandidat baru lalu rerun supaya selectbox pindah ke "Center peta"
            st.session_state["_cands"] = [{"label": "Center peta", "lat": cen_lat, "lon": cen_lon}]
            st.rerun()
