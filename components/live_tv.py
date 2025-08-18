import requests
import streamlit as st

def render_live_tv_tab():
    st.subheader("📺 Live TV — Makkah & Madinah")

    makkah_iframe = """
    <iframe width="818" height="587" src="https://www.youtube.com/embed/sJHSo9sYdeI" title="🔴 Makkah Live | مكة مباشر | الحرم المكي مباشر | قناة القران الكريم السعودية مباشر | مكه المكرمه مبا" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    """

    madinah_iframe = """
    <iframe width="818" height="587" src="https://www.youtube.com/embed/wiQWH8908PU" title="Madina Live | Madinah Live TV Online | Masjid Al Nabawi Live HD | Madinah Live Today 24/7" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    """

    choice = st.selectbox("Pilih Channel", ["Makkah", "Madinah"])
    if choice == "Makkah":
        st.markdown(makkah_iframe, unsafe_allow_html=True)
    else:
        st.markdown(madinah_iframe, unsafe_allow_html=True)

