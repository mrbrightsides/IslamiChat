import time, math, requests, streamlit as st

OZT_TO_GRAM = 31.1034768

@st.cache_data(ttl=6*3600)
def fetch_gold_price_idr_per_gram() -> tuple[float, str]:
    """
    Balik (harga_emas_idr_per_gram, sumber_info).
    Melempar Exception kalau semua sumber gagal (biar UI bisa fallback).
    """
    # 1) GoldAPI: XAU/USD per ozt  -> butuh API key
    key = st.secrets.get("GOLDAPI_KEY", "")
    if key:
        r = requests.get(
            "https://www.goldapi.io/api/XAU/USD",
            headers={"x-access-token": key, "User-Agent": "IslamiChat/1.0"},
            timeout=10,
        )
        if r.ok:
            data = r.json()
            price_usd_per_ozt = float(data.get("price"))
            # 2) USD→IDR
            fx = requests.get(
                "https://api.exchangerate.host/latest",
                params={"base": "USD", "symbols": "IDR"},
                timeout=10,
            ).json()
            usd_idr = float(fx["rates"]["IDR"])
            price_idr_per_gram = price_usd_per_ozt * usd_idr / OZT_TO_GRAM
            return price_idr_per_gram, "GoldAPI + exchangerate.host"

    # 3) (opsional) tambahkan sumber lain kalau punya API key lain
    raise Exception("Semua sumber otomatis gagal.")

def format_rp(x: float) -> str:
    return f"Rp {x:,.0f}".replace(",", ".")

def nisab_emas_idr(emas_idr_per_gram: float, tahunan: bool) -> float:
    nisab_tahunan = 85.0 * emas_idr_per_gram
    return nisab_tahunan if tahunan else nisab_tahunan / 12.0

def zakat_kalkulator():
    st.subheader("💰 Kalkulator Zakat Penghasilan")

    # === HARGA EMAS: otomatis + fallback manual ===
    col0a, col0b = st.columns([1,1])
    with col0a:
        use_auto = st.toggle("Gunakan harga emas otomatis", value=True,
                             help="Butuh GOLDAPI_KEY di st.secrets. Fallback ke input manual jika gagal.")
    with col0b:
        if st.button("🔄 Reload harga emas"):
            fetch_gold_price_idr_per_gram.clear()

    auto_price, source = None, ""
    auto_err = None
    if use_auto:
        try:
            auto_price, source = fetch_gold_price_idr_per_gram()
        except Exception as e:
            auto_err = str(e)

    # input penghasilan
    penghasilan = st.number_input("Total Penghasilan Bulanan (Rp)", min_value=0, step=1000, value=0)
    pengeluaran = st.number_input("Pengeluaran Pokok Bulanan (Rp)", min_value=0, step=1000, value=0)

    # harga emas manual bila auto gagal / dinonaktifkan
    emas_per_gram = st.number_input(
        "Harga Emas/gram Saat Ini (Rp)",
        min_value=0, step=1000,
        value= int(auto_price) if (use_auto and auto_price) else 1_000_000
    )

    if use_auto and auto_price:
        st.caption(f"📈 Harga emas otomatis: {format_rp(auto_price)} / gram  •  sumber: {source}")
    elif use_auto and auto_err:
        st.warning(f"Gagal ambil harga emas otomatis: {auto_err}")
        st.caption("Gunakan nilai manual di atas.")

    with st.expander("Pengaturan Perhitungan", expanded=False):
        metode = st.radio("Metode", ["Bulanan (Penghasilan)", "Tahunan (Maal)"], horizontal=True)
        pakai_nisab = st.checkbox("Terapkan syarat nisab", value=True)

    if st.button("Hitung Zakat", type="primary"):
        saldo = max(penghasilan - pengeluaran, 0)
        nisab = nisab_emas_idr(emas_per_gram, tahunan=(metode=="Tahunan (Maal)"))
        wajib = (saldo >= nisab) if pakai_nisab else True
        zakat = 0.025 * saldo if wajib else 0

        st.markdown("---")
        st.write(f"💡 Nisab acuan: {format_rp(nisab)} "
                 f"({'85 gr emas' if metode=='Tahunan (Maal)' else '≈ 85 gr / 12'})")
        st.write(f"📦 Saldo kena zakat: {format_rp(saldo)}")
        if wajib:
            st.success(f"✅ Wajib zakat. Jumlah zakat (2.5%): **{format_rp(zakat)}**")
        else:
            st.info("ℹ️ Belum mencapai nisab, belum wajib zakat.")

