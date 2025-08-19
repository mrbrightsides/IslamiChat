# components/zikir.py
import streamlit as st
from streamlit.components.v1 import html
from urllib.parse import quote_plus

PHRASES = [
    ("Subhanallah", "سُبْحَانَ اللَّه"),
    ("Alhamdulillah", "الْحَمْدُ لِلَّه"),
    ("Allahu Akbar", "اللَّهُ أَكْبَر"),
    ("Lā ilāha illallāh", "لَا إِلٰهَ إِلَّا اللَّه"),
    ("Astaghfirullah", "أَسْتَغْفِرُ اللَّه"),
    ("Shalawat", "اللَّهُمَّ صَلِّ عَلَى مُحَمَّد"),
]

def _wa(text: str) -> str:
    return f"https://wa.me/?text={quote_plus(text)}"

def _haptic():
    # getar pendek di Android (kalau didukung)
    html("<script>if(navigator.vibrate){navigator.vibrate(15)}</script>", height=0)

def show_zikir_tab():
    st.title("🧿 Tasbih / Penghitung Zikir")
    st.caption("Tap tombol besar untuk menghitung. Progress tersimpan selama sesi ini.")

    # ------- STATE ----------
    z = st.session_state.setdefault("zikir", {
        "phrase": PHRASES[0][0],
        "target": 33,
        "count": 0,
        "haptic": True,
    })

    # ------- PILIHAN & TARGET ----------
    c1, c2 = st.columns([3, 2])
    with c1:
        phrase = st.selectbox(
            "Pilih dzikir",
            [p[0] for p in PHRASES],
            index=[p[0] for p in PHRASES].index(z["phrase"]),
        )
        if phrase != z["phrase"]:
            z["phrase"] = phrase
            z["count"] = 0  # ganti frasa → reset hitungan
    with c2:
        tgt = st.number_input("Target (0 = tanpa batas)", min_value=0, value=int(z["target"]), step=1)
        z["target"] = int(tgt)

    z["haptic"] = st.toggle("Getar saat +1 (Android)", value=z.get("haptic", True))

    # ------- GAYA BESAR ----------
    st.markdown("""
    <style>
      .counter-box{font-size:46px; text-align:center; margin:8px 0 14px 0;}
      .big button{font-size:28px; padding:18px 0; width:100%;}
      .ghost{visibility:hidden; height:0; margin:0; padding:0;}
    </style>
    """, unsafe_allow_html=True)

    # ------- TAMPILAN COUNTER ----------
    arab = next((p[1] for p in PHRASES if p[0]==z["phrase"]), "")
    st.write(f"**{z['phrase']}**  &nbsp; <span style='color:#bbb'>{arab}</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='counter-box'><b>{z['count']}</b> / {('∞' if z['target']==0 else z['target'])}</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1, 2, 1])
    with b1:
        if st.button("↩️ -1", use_container_width=True):
            z["count"] = max(0, z["count"]-1)
    with b2:
        if st.button("🟢  +1", use_container_width=True):
            z["count"] += 1
            if z.get("haptic", True):
                _haptic()
    with b3:
        if st.button("♻️ Reset", use_container_width=True):
            z["count"] = 0

    # Progress
    if z["target"] > 0:
        st.progress(min(1.0, z["count"]/max(1, z["target"])))
        if z["count"] >= z["target"]:
            st.success("Alhamdulillah, target tercapai!")
            st.balloons()

    # ------- SHARE WHATSAPP ----------
    ringkas = f"Saya telah berdzikir {z['phrase']} sebanyak {z['count']}x."
    st.link_button("Kirim ringkasan ke WhatsApp", _wa(ringkas), use_container_width=True)

    st.divider()

    # ====== MODE RANGKAIAN SETELAH SHALAT ======
    with st.expander("🕌 Rangkaian setelah shalat (33–33–33–1)", expanded=False):
        seq = st.session_state.setdefault("zikir_seq", {"s":0, "h":0, "a":0, "t":0})
        def blok(label, key, target):
            st.write(f"**{label}**  — target **{target}**")
            c1, c2, c3 = st.columns([1,2,1])
            c1.metric("Saat ini", seq[key])
            if c2.button(" +1 ", key=f"inc_{key}"): 
                seq[key]+=1; _haptic()
            if c3.button(" Reset ", key=f"res_{key}"): 
                seq[key]=0
            st.progress(min(1.0, seq[key]/target))
            st.markdown("<div class='ghost'>.</div>", unsafe_allow_html=True)

        blok("Subhanallah", "s", 33)
        blok("Alhamdulillah", "h", 33)
        blok("Allahu Akbar", "a", 33)
        blok("Lā ilāha illallāh (tamam)", "t", 1)

        if seq["s"]>=33 and seq["h"]>=33 and seq["a"]>=33 and seq["t"]>=1:
            st.success("Rangkaian selesai. Semoga berkah 🌙")
            st.balloons()
