import streamlit as st
from math import radians, degrees, sin, cos, atan2
from geopy.geocoders import Nominatim

def show_qibla_direction():
    st.subheader("🧭 Arah Kiblat")

    lokasi = st.text_input("Masukkan Nama Lokasi", placeholder="contoh: Jakarta, Indonesia")

    if lokasi:
        geo = Nominatim(user_agent="kiblat-app")
        loc = geo.geocode(lokasi)
        if loc:
            lat_user, lon_user = loc.latitude, loc.longitude
            lat_kabah, lon_kabah = 21.4225, 39.8262

            delta_lon = radians(lon_kabah - lon_user)
            lat1 = radians(lat_user)
            lat2 = radians(lat_kabah)

            x = sin(delta_lon)
            y = cos(lat1) * tan(lat2) - sin(lat1) * cos(delta_lon)
            arah = atan2(x, y)
            kiblat_deg = (degrees(arah) + 360) % 360

            st.success(f"🧭 Arah Kiblat dari {lokasi}: {kiblat_deg:.2f}° dari Utara")
        else:
            st.error("Lokasi tidak ditemukan.")
