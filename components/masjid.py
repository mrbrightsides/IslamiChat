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
        timeout=(6, 20),  # (connect, read)
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
                    time.sleep(delay); delay *= 1.6
                    continue
                r.raise_for_status()
                return r.json().get("elements", [])
            except Exception as e:
                last_err.append(f"{ep} try{attempt+1}: {e}")
                time.sleep(delay); delay *= 1.6
    raise RuntimeError("Overpass gagal: " + " | ".join(last_err[:3]) + " …")

# ===== Geocoding (multi kandidat + fallback) =====
@st.cache_data(ttl=3600)
def geocode_candidates(q: str, country_bias: str | None = "id"):
    geo = Nominatim(user_agent="islamiChat/1.0", timeout=10)
    # coba full query
    results = geo.geocode(
        q, language="id", addressdetails=True, exactly_one=False, limit=5,
        country_codes=country_bias
    )
    # fallback ke bagian paling akhir (biasanya kota) kalau kosong
    if not results and "," in q:
        tail = q.split(",")[-1].strip()
        if tail:
            results = geo.geocode(
                tail, language="id", addressdetails=True, exactly_one=False, limit=5,
                country_codes=country_bias
            )
    if not results:
        return []
    return [{"label": r.address, "lat": float(r.latitude), "lon": float(r.longitude)} for r in results]

# ===== UI utama =====
def show_nearby_mosques():
    st.header("🕌 Masjid Terdekat")

    radius = st.slider("Radius pencarian (meter)", 300, 4000, 1500, step=100)
    lite = st.toggle("Gunakan query ringan (lebih mudah lolos rate-limit)", value=False)

    # Satu tempat input alamat
    q = st.text_input(
        "Masukkan alamat/lokasi (contoh: **8 Ilir, Palembang** atau **Sekayu, Musi Banyuasin**)",
        value=st.session_state.get("addr_query", ""),
        placeholder="Kelurahan, Kota",
        key="addr_query",
    )

    cari_click = st.button("🔎 Cari alamat")

    # State penyimpanan kandidat & indeks pilihan
    if "cands" not in st.session_state:
        st.session_state.cands = []
    if "cand_idx" not in st.session_state:
        st.session_state.cand_idx = 0
    if "addr_query_prev" not in st.session_state:
        st.session_state.addr_query_prev = ""

    # Geocode hanya ketika tombol ditekan atau teks berubah (dan tidak kosong)
    if (cari_click or (q and q != st.session_state.addr_query_prev)) and q.strip():
        st.session_state.cands = geocode_candidates(q.strip())
        st.session_state.cand_idx = 0
        st.session_state.addr_query_prev = q

    # Jika belum ada pencarian → stop (tidak auto-load Palembang)
    if not st.session_state.cands:
        st.info("Masukkan alamat, lalu klik **Cari alamat**.")
        return

    # Pilih kandidat (muncul hanya setelah ada hasil)
    labels = [c["label"] for c in st.session_state.cands]
    st.session_state.cand_idx = st.selectbox(
        "Pilih lokasi yang sesuai:",
        range(len(labels)),
        format_func=lambda i: labels[i],
        index=st.session_state.cand_idx,
        key="cand_idx_select",
    )

    cand = st.session_state.cands[st.session_state.cand_idx]
    lat, lon, label = cand["lat"], cand["lon"], cand["label"]
    st.caption(f"Lokasi dipilih: {label} • ({lat:.5f}, {lon:.5f})")

    # Ambil data masjid
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

    # Peta di tengah halaman
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

    # render map di kolom tengah (centered)
    left, mid, right = st.columns([1, 6, 1])
    with mid:
        st_folium(m, width=800, height=520)
