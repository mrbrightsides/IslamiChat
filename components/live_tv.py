import requests
import streamlit as st

def render_live_tv_tab():
    st.subheader("📺 Live TV — Makkah & Madinah")

    makkah_iframe = """
    <iframe width="100%" height="480"
    src="https://www.youtube.com/embed/live_stream?channel=UC_y7dU8PSVtSxVY6_0O2hjQ"
    title="Masjidil Haram Live" frameborder="0" allowfullscreen></iframe>
    """

    madinah_iframe = """
    <iframe width="100%" height="480"
    src="https://www.youtube.com/embed/live_stream?channel=UCnJq7FkM0fgQHO1kU6clh8A"
    title="Masjid Nabawi Live" frameborder="0" allowfullscreen></iframe>
    """

    choice = st.selectbox("Pilih Channel", ["Makkah", "Madinah"])
    if choice == "Makkah":
        st.markdown(makkah_iframe, unsafe_allow_html=True)
    else:
        st.markdown(madinah_iframe, unsafe_allow_html=True)

