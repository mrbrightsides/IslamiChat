import streamlit as st
from tools_mushaf import MUSHAF
from tools_hafalan import diff_ratio, word_diffs

def show_hafalan_tab():
    st.title("🎙️ Setor Hafalan — MVP")
    st.caption("Pilih mode input: ketik **Latin** (tanpa keyboard Arab) atau **tempel teks Arab**. "
               "Audio upload disiapkan sebagai next step.")

    # Mode input
    mode = st.radio("Mode input", ["Ketik Latin (tanpa harakat)", "Tempel teks Arab", "Upload Audio (segera)"],
                    horizontal=True)

    # Pilih Surah + Range Ayat
    surah = st.selectbox("Pilih Surah:", list(MUSHAF.keys()),
                         format_func=lambda x: f"{x} — {MUSHAF[x]['name']}")
    ayahs = MUSHAF[surah]["ayahs"]
    start, end = st.select_slider("Pilih range ayat:",
                                  options=list(ayahs.keys()),
                                  value=(list(ayahs.keys())[0], list(ayahs.keys())[-1]))

    is_latin = (mode.startswith("Ketik Latin"))
    is_arab  = (mode.startswith("Tempel"))
    # Placeholder untuk audio (coming soon)
    if mode.startswith("Upload Audio"):
        st.info("🎧 Fitur upload audio akan ditambahkan selanjutnya (STT → cek otomatis).")
        return

    st.divider()
    for i in range(int(start), int(end)+1):
        target = ayahs[str(i)]
        with st.container(border=True):
            st.markdown(f"**Ayat {i} — Target:** {target}")

            if is_latin:
                user_text = st.text_input("Ketik Latin (contoh: *bismillah arrahman arrahim*)", key=f"latin{i}")
                mode_key = "latin"
            else:
                user_text = st.text_input("Tempel teks Arab (tanpa harakat juga boleh)", key=f"arab{i}")
                mode_key = "arabic"

            if user_text:
                score = diff_ratio(target, user_text, mode=mode_key)
                st.write(f"🎯 Akurasi: **{score*100:.1f}%**")

                diffs = word_diffs(target, user_text, mode=mode_key)
                if diffs:
                    st.error(f"Perbedaan: {diffs}")
                else:
                    st.success("✅ Bacaan sesuai!")
