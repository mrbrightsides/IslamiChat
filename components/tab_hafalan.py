import streamlit as st
from tools_mushaf import MUSHAF
from tools_hafalan import diff_ratio, word_diffs

def show_hafalan_tab():
    st.title("📖 Setor Hafalan (Demo)")

    # Pilih surat & ayat
    surah = st.selectbox("Pilih Surah:", list(MUSHAF.keys()), format_func=lambda x: MUSHAF[x]["name"])
    ayahs = MUSHAF[surah]["ayahs"]

    start, end = st.select_slider(
        "Pilih range ayat:",
        options=list(ayahs.keys()),
        value=(list(ayahs.keys())[0], list(ayahs.keys())[-1])
    )

    st.info("Untuk demo awal, masukkan teks bacaan manual (nanti diganti hasil STT).")

    for i in range(int(start), int(end)+1):
        target = ayahs[str(i)]
        st.markdown(f"### Ayat {i}")
        st.markdown(f"**Target:** {target}")

        user_text = st.text_input(f"Teks bacaan kamu (ayat {i}):", key=f"t{i}")
        if user_text:
            score = diff_ratio(target, user_text)
            st.write(f"🎯 Akurasi: `{score*100:.1f}%`")

            diffs = word_diffs(target, user_text)
            if diffs:
                st.error(f"Perbedaan: {diffs}")
            else:
                st.success("✅ Bacaan sesuai!")
