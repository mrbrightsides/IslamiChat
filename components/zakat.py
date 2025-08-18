import streamlit as st

def zakat_kalkulator():
    st.subheader("💰 Kalkulator Zakat Penghasilan")

    penghasilan = st.number_input("Total Penghasilan Bulanan (Rp)", min_value=0)
    pengeluaran = st.number_input("Pengeluaran Pokok Bulanan (Rp)", min_value=0)
    emas_per_gram = st.number_input("Harga Emas/gram Saat Ini (Rp)", value=1000000)

    if st.button("Hitung Zakat"):
        zakat_nisab = 85 * emas_per_gram
        saldo = penghasilan - pengeluaran
        wajib_zakat = saldo >= zakat_nisab
        zakat = 0.025 * saldo if wajib_zakat else 0

        st.markdown("---")
        st.write(f"💡 Nisab Zakat: Rp {zakat_nisab:,.0f}")
        st.write(f"📦 Saldo kena zakat: Rp {saldo:,.0f}")
        if wajib_zakat:
            st.success(f"✅ Wajib Zakat. Jumlah zakat: Rp {zakat:,.0f}")
        else:
            st.info("ℹ️ Belum mencapai nisab, belum wajib zakat.")
