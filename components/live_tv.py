import streamlit as st

MAKKAH_EMBED = "https://www.youtube.com/embed/bNY8a2BB5Gc"
MADINAH_EMBED = "https://www.youtube.com/embed/wiQWH8908PU"

def _responsive_embed(embed_url: str, title: str) -> str:
    """
    Iframe responsif 16:9 (cocok mobile/desktop).
    - Container pakai trik padding-bottom 56.25% (16:9).
    - Iframe absolute full width/height.
    """
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
    st.subheader("📺 Live TV — Makkah & Madinah")
    st.caption("Streaming resmi via YouTube. Jika tidak muncul, coba refresh atau buka langsung di aplikasi YouTube.")

    choice = st.selectbox("Pilih Channel", ["Makkah (Masjidil Haram)", "Madinah (Masjid Nabawi)"])

    if "Makkah" in choice:
        st.markdown(_responsive_embed(MAKKAH_EMBED, "Makkah Live"), unsafe_allow_html=True)
        
    else:
        st.markdown(_responsive_embed(MADINAH_EMBED, "Madinah Live"), unsafe_allow_html=True)
