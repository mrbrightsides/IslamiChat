import streamlit as st

CHANNELS = {
    "Makkah (Masjidil Haram)": {
        "url": "https://www.youtube.com/embed/bNY8a2BB5Gc",
        "title": "Makkah Live"
    },
    "Madinah (Masjid Nabawi)": {
        "url": "https://www.youtube.com/embed/TpT8b8JFZ6E",
        "title": "Madinah Live"
    },
    "Quran1 (Sheikh Mishary Rashid Alafasy)": {
        "url": "https://www.youtube.com/embed/lCeoYw3Y9zM",
        "title": "Quran Recitation"
    },
    "Quran2 (Saad Al-Ghamdi)": {
        "url": "https://www.youtube.com/embed/hBRkEE96geE",
        "title": "Quran Recitation"
    },
    "Quran3 (Alaa Aqel)": {
        "url": "https://www.youtube.com/embed/9shisvrYqXM",
        "title": "Quran Recitation"
    }
}

def _responsive_embed(embed_url: str, title: str) -> str:
    return f"""
    <div style="position:relative;width:100%;max-width:980px;margin:0 auto;">
      <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.25);">
        <iframe
          src="{embed_url}"
          title="{title}"
          style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowfullscreen
        ></iframe>
      </div>
    </div>
    """

def render_live_tv_tab():
    st.subheader("📺 Live TV — Makkah, Madinah, dan Quran Recitation")
    st.caption("Streaming resmi via YouTube. Jika tidak muncul, coba refresh atau buka langsung di aplikasi YouTube.")

    choice = st.selectbox("Pilih Channel", list(CHANNELS.keys()))
    channel_info = CHANNELS[choice]
    st.markdown(_responsive_embed(channel_info["url"], channel_info["title"]), unsafe_allow_html=True)
