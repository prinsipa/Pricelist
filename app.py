import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Kabel", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Kabel")
st.write(
    "Data harga di bawah ini diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil data dari semua sheet secara dinamis
@st.cache_data(ttl=60)
def load_all_sheets():
    # ID dari Google Spreadsheet baru Anda
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Daftar sheet / tab yang ada di spreadsheet Anda
    # Anda bisa menambah atau mengubah nama sheet di sini sesuai kebutuhan
    sheet_names = [
        "NYM",
        "NYY",
        "NYA",
        "Aluminium",
        "Inverter",
        "Solar PV",
        "Mounting PV",
    ]
    all_data = []

    for sheet in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df_temp = pd.read_csv(url)

            # Buang kolom kosong / Unnamed
            df_temp = df_temp.loc[
                :, ~df_temp.columns.str.contains("^Unnamed")
            ]

            # Tentukan Kategori Produk berdasarkan nama sheet
            if sheet.lower() in ["nym", "nyy", "nya", "aluminium", "kabel"]:
                kategori_nama = "Kabel"
            else:
                kategori_nama = (
                    sheet  # Untuk Inverter, Solar PV, Mounting PV, dll.
                )

            # Tambahkan kolom Kategori di posisi paling depan
            df_temp.insert(0, "Kategori Produk", kategori_nama)

            all_data.append(df_temp)
        except Exception:
            # Jika sheet belum dibuat di spreadsheet, lewati tanpa error
            pass

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined = df_combined.dropna(how="all")
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    # Sidebar Filter Kategori & Pencarian
    st.sidebar.header("🔍 Filter Kategori & Produk")

    # Dropdown Pilihan Kategori Produk
    if "Kategori Produk" in df.columns:
        kategori_list = ["Semua Kategori"] + list(
            df["Kategori Produk"].dropna().unique()
        )
        pilih_kategori = st.sidebar.selectbox(
            "Pilih Kategori Produk:", kategori_list
        )
        if pilih_kategori != "Semua Kategori":
            df = df[df["Kategori Produk"] == pilih_kategori]

    # Filter Pencarian Fleksibel
    search_query = st.sidebar.text_input(
        "Cari Ukuran / Tipe / Spesifikasi:", ""
    )
    if search_query:
        clean_query = search_query.lower().replace(" ", "")

        def match_row(row):
            row_str = "".join(row.astype(str)).lower().replace(" ", "")
            return clean_query in row_str

        df = df[df.apply(match_row, axis=1)]

    # Menampilkan informasi jumlah data dan tabel
    st.info(f"Menampilkan {len(df)} data produk.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Gagal memuat data. Error: {e}")
