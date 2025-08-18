import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        loc = data.get("loc", "").split(",")
        if len(loc) == 2:
            return float(loc[0]), float(loc[1])
    except Exception as e:
        st.error("Gagal mendapatkan lokasi: " + str(e))
    return None, None

def show_nearby_mosques():
    st.header("🕌 Masjid Terdekat")

    lat, lon = get_user_location()
    if lat is None or lon is None:
        st.warning("Tidak dapat menentukan lokasi Anda.")
        return

    m = folium.Map(location=[lat, lon], zoom_start=14)
    folium.Marker([lat, lon], tooltip="Lokasi Anda", icon=folium.Icon(color="blue")).add_to(m)

    # Fetch masjid nearby from OpenStreetMap using Overpass API
    query = f"""
    [out:json];
    (
      node["amenity"="place_of_worship"]["name"](around:3000,{lat},{lon});
      way["amenity"="place_of_worship"]["name"](around:3000,{lat},{lon});
      relation["amenity"="place_of_worship"]["name"](around:3000,{lat},{lon});
    );
    out center;
    """

    try:
        res = requests.post("https://overpass-api.de/api/interpreter", data={"data": query})
        mosques = res.json()["elements"]

        for mosque in mosques:
            name = mosque["tags"].get("name", "Masjid")
            lat_m = mosque.get("lat") or mosque.get("center", {}).get("lat")
            lon_m = mosque.get("lon") or mosque.get("center", {}).get("lon")
            if lat_m and lon_m:
                folium.Marker([lat_m, lon_m], tooltip=name, icon=folium.Icon(color="green", icon="info-sign")).add_to(m)

    except Exception as e:
        st.error("Gagal mengambil data masjid terdekat: " + str(e))

    st_folium(m, width=700, height=500)

if __name__ == "__main__":
    show_nearby_mosques()
