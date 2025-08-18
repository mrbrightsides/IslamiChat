import streamlit as st

def rupiah(x: float) -> str:
    return f"Rp {x:,.0f}".replace(",", ".")

def zakat_kalkulator():
    st.subheader("💰 Kalkulator Zakat Penghasilan")

    # --- Input
    penghasilan = st.number_input("Total Penghasilan Bulanan (Rp)", min_value=0, step=1000, value=0)
    pengeluaran = st.number_input("Pengeluaran Pokok Bulanan (Rp)", min_value=0, step=1000, value=0)
    emas_per_gram = st.number_input("Harga Emas/gram Saat Ini (Rp)", min_value=0, step=1000, value=1000000)

    with st.expander("Pengaturan Perhitungan", expanded=False):
        metode = st.radio(
            "Metode",
            ["Bulanan (Penghasilan)", "Tahunan (Maal)"],
            horizontal=True,
            help="Bulanan: nisab = 85gr emas / 12. Tahunan: nisab = 85gr emas penuh."
        )
        pakai_nisab = st.checkbox("Terapkan syarat nisab", value=True,
                                  help="Nonaktifkan jika ingin tetap menghitung 2.5% dari saldo meski belum mencapai nisab.")

    if st.button("Hitung Zakat", type="primary"):
        # --- Perhitungan dasar
        saldo = max(penghasilan - pengeluaran, 0)

        nisab_tahunan = 85 * emas_per_gram
        nisab = nisab_tahunan if metode == "Tahunan (Maal)" else nisab_tahunan / 12

        wajib_zakat = (saldo >= nisab) if pakai_nisab else True
        zakat = 0.025 * saldo if wajib_zakat else 0

        # --- Output
        st.markdown("---")
        st.write(f"💡 Nisab acuan: {rupiah(nisab)}  "
                 f"({'85 gr emas' if metode=='Tahunan (Maal)' else '≈ (85 gr / 12) emas'})")
        st.write(f"📦 Saldo kena zakat: {rupiah(saldo)}")

        if wajib_zakat:
            st.success(f"✅ Wajib zakat. Jumlah zakat (2.5%): **{rupiah(zakat)}**")
        else:
            st.info("ℹ️ Belum mencapai nisab, belum wajib zakat menurut pengaturan saat ini.")
            st.caption("Tip: nonaktifkan opsi *Terapkan syarat nisab* jika ingin tetap menunaikan 2.5% dari saldo.")
