import requests, math, streamlit as st

OZT_TO_GRAM = 31.1034768

@st.cache_data(ttl=6*3600)
def fetch_gold_price_idr_per_gram() -> tuple[float, str]:
    """
    Ambil harga emas/gram (IDR). Urutan:
      A) GoldAPI XAU/IDR: price_gram_24k -> fallback price/ozt / 31.1034768
      B) GoldAPI XAU/USD + kurs USD→IDR (open.er-api.com)
    Return: (harga_idr_per_gram, sumber_info)
    Raise Exception bila seluruh langkah gagal.
    """
    key = st.secrets.get("GOLDAPI_KEY", "")
    if not key:
        raise Exception("GOLDAPI_KEY tidak ada di secrets")

    headers = {"x-access-token": key, "User-Agent": "IslamiChat/1.0"}

    # --- A) Langsung XAU/IDR ---
    try:
        r = requests.get("https://www.goldapi.io/api/XAU/IDR", headers=headers, timeout=10)
        data = r.json()
        if "error" in data:
            # tampilkan error aslinya untuk debugging di UI
            raise Exception(f"GoldAPI XAU/IDR error: {data.get('error')}")
        pg = data.get("price_gram_24k")
        if pg:
            val = float(pg)
            if math.isfinite(val) and val > 0:
                return val, "GoldAPI XAU/IDR • price_gram_24k"
        p_ozt = data.get("price")
        if p_ozt:
            val = float(p_ozt) / OZT_TO_GRAM
            if math.isfinite(val) and val > 0:
                return val, "GoldAPI XAU/IDR • price/oz → /gram"
    except Exception as e:
        # biarkan lanjut ke fallback, tapi catat pesan
        last_err_A = str(e)
    else:
        last_err_A = "Tidak ada field harga yang valid dari XAU/IDR"

    # --- B) XAU/USD + konversi kurs ---
    try:
        r = requests.get("https://www.goldapi.io/api/XAU/USD", headers=headers, timeout=10)
        data = r.json()
        if "error" in data:
            raise Exception(f"GoldAPI XAU/USD error: {data.get('error')}")
        # ambil harga per ozt dalam USD, atau langsung per gram jika tersedia
        pg_usd = data.get("price_gram_24k")
        if pg_usd:
            usd_per_gram = float(pg_usd)
        else:
            p_ozt_usd = float(data["price"])  # naikkan KeyError bila tak ada → ketangkap except
            usd_per_gram = p_ozt_usd / OZT_TO_GRAM

        fx = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
        usd_idr = float(fx["rates"]["IDR"])
        idr_per_gram = usd_per_gram * usd_idr
        if math.isfinite(idr_per_gram) and idr_per_gram > 0:
            return idr_per_gram, "GoldAPI XAU/USD + open.er-api.com"
        raise Exception("Nilai kurs/konversi tidak valid")
    except Exception as e:
        last_err_B = str(e)

    # --- Semua gagal ---
    raise Exception(f"Gagal ambil harga emas otomatis. A: {last_err_A} | B: {last_err_B}")

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
        use_auto = st.toggle("Gunakan harga emas otomatis", value=False,
                             help="Gunakan harga emas manual jika data otomatis tidak tersedia.")
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

