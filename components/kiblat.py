import streamlit as st
from math import radians, degrees, sin, cos, atan2
from geopy.geocoders import Nominatim

KAABA_LAT = 21.422487
KAABA_LON = 39.826206

@st.cache_data(ttl=86400)
def geocode_cached(q: str):
    """Geocode dengan cache (1 hari)."""
    geo = Nominatim(user_agent="islamiChat/1.0", timeout=10)
    loc = geo.geocode(q, language="id")
    if not loc:
        return None
    return (loc.latitude, loc.longitude, loc.address)

def qibla_bearing(lat: float, lon: float) -> float:
    """Bearing (0–360° dari utara, searah jarum jam) menuju Ka'bah."""
    φ1, λ1 = radians(lat), radians(lon)
    φ2, λ2 = radians(KAABA_LAT), radians(KAABA_LON)
    Δλ = λ2 - λ1
    y = sin(Δλ) * cos(φ2)
    x = cos(φ1) * sin(φ2) - sin(φ1) * cos(φ2) * cos(Δλ)
    θ = (degrees(atan2(y, x)) + 360) % 360
    return θ

def show_qibla_direction():
    st.subheader("🧭 Arah Kiblat")
    lokasi = st.text_input("Masukkan Nama Lokasi", placeholder="contoh: Jakarta, Indonesia")

    if not lokasi.strip():
        return

    geo = geocode_cached(lokasi)
    if not geo:
        st.error("Lokasi tidak ditemukan. Coba perjelas nama lokasi.")
        return

    lat_user, lon_user, addr = geo
    bearing = qibla_bearing(lat_user, lon_user)

    st.success(f"📍 {addr}\n\n🧭 Arah Kiblat: **{bearing:.2f}°** dari utara (searah jarum jam).")
