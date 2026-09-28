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


# Fungsi untuk mengambil dan menggabungkan semua sheet kategori produk
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Masukkan SEMUA nama sheet/tab yang ada di spreadsheet Anda di sini
    sheet_names = ["NYM", "NYY", "NYA", "Inverter", "Solar PV", "Mounting PV"]

    all_data = []

    for sheet in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df_temp = pd.read_csv(url)

            # Buang kolom yang tidak bernama / Unnamed
            df_temp = df_temp.loc[
                :, ~df_temp.columns.str.contains("^Unnamed")
            ]

            # Pastikan kolom Kategori/Jenis Produk terisi dari nama sheet jika belum ada
            if "Kategori" not in df_temp.columns and "Jenis Kabel" not in df_temp.columns:
                df_temp.insert(0, "Kategori Produk", sheet)
            elif "Jenis Kabel" in df_temp.columns:
                df_temp = df_temp.rename(columns={"Jenis Kabel": "Tipe/Model"})
                df_temp.insert(0, "Kategori Produk", sheet)

            all_data.append(df_temp)
        except Exception as e:
            print(f"Sheet {sheet} tidak ditemukan atau kosong: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined = df_combined.dropna(how="all")
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    # Sidebar Filter Pencarian
    st.sidebar.header("🔍 Filter Kategori & Produk")

    # Dropdown Filter Kategori Produk (Inverter, Solar PV, Mounting, Kabel, dll.)
    if "Kategori Produk" in df.columns:
        kategori_list = ["Semua Kategori"] + list(
            df["Kategori Produk"].dropna().unique()
        )
        pilih_kategori = st.sidebar.selectbox(
            "Pilih Kategori Produk:", kategori_list
        )
        if pilih_kategori != "Semua Kategori":
            df = df[df["Kategori Produk"] == pilih_kategori]

    # Filter Pencarian Bebas (Nama / Model / Ukuran / Spesifikasi)
    search_query = st.sidebar.text_input(
        "Cari Tipe / Spesifikasi / Ukuran:", ""
    )
    if search_query:
        clean_query = search_query.lower().replace(" ", "")

        def match_row(row):
            row_str = "".join(row.astype(str)).lower().replace(" ", "")
            return clean_query in row_str

        df = df[df.apply(match_row, axis=1)]

    # Menampilkan informasi jumlah data dan tabel interaktif
    st.info(f"Menampilkan {len(df)} data produk.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Gagal memuat data. Error: {e}")
