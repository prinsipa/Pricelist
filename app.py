import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Kabel", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Material")
st.write(
    "Data harga diambil secara real-time dari Google Spreadsheet perusahaan."
)


# Fungsi untuk mengambil data dari semua sheet secara dinamis
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Daftar tab/sheet sesuai dengan gambar spreadsheet Anda
    sheet_names = ["Kabel Cu", "Kabel AL", "Inverter", "Solar PV", "Mounting PV"]
    all_data = []

    for sheet in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df_temp = pd.read_csv(url)

            # Buang kolom kosong / Unnamed
            df_temp = df_temp.loc[
                :, ~df_temp.columns.str.contains("^Unnamed")
            ]

            # Tentukan Kategori Utama berdasarkan nama sheet
            if "Kabel" in sheet:
                kategori_nama = "Kabel"
                # Deteksi jenis konduktor berdasarkan nama tab atau isi spesifikasi
                if "AL" in sheet.upper():
                    df_temp.insert(0, "Konduktor", "AL (Aluminium)")
                else:
                    df_temp.insert(0, "Konduktor", "CU (Tembaga)")
            else:
                kategori_nama = sheet  # Inverter, Solar PV, Mounting PV, dll.

            # Tambahkan kolom Kategori Produk di posisi paling depan
            df_temp.insert(0, "Kategori Produk", kategori_nama)

            all_data.append(df_temp)
        except Exception:
            pass

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined = df_combined.dropna(how="all")
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    # Sidebar Filter
    st.sidebar.header("🔍 Filter Pencarian Produk")

    # 1. Filter Kategori Produk Utama
    if "Kategori Produk" in df.columns:
        kategori_list = ["Semua Kategori"] + list(
            df["Kategori Produk"].dropna().unique()
        )
        pilih_kategori = st.sidebar.selectbox(
            "Pilih Kategori Produk:", kategori_list
        )
        if pilih_kategori != "Semua Kategori":
            df = df[df["Kategori Produk"] == pilih_kategori]

    # 2. Jika Kategori adalah Kabel, tampilkan filter Konduktor (AL / CU) & Jenis Kabel
    if pilih_kategori == "Kabel" or pilih_kategori == "Semua Kategori":
        if "Konduktor" in df.columns:
            konduktor_list = ["Semua"] + list(
                df["Konduktor"].dropna().unique()
            )
            pilih_konduktor = st.sidebar.selectbox(
                "Pilih Jenis Konduktor:", konduktor_list
            )
            if pilih_konduktor != "Semua":
                df = df[df["Konduktor"] == pilih_konduktor]

        if "Jenis Kabel" in df.columns:
            jenis_kabel_list = ["Semua"] + list(
                df["Jenis Kabel"].dropna().unique()
            )
            pilih_jenis_kabel = st.sidebar.selectbox(
                "Pilih Jenis Kabel:", jenis_kabel_list
            )
            if pilih_jenis_kabel != "Semua":
                df = df[df["Jenis Kabel"] == pilih_jenis_kabel]

    # 3. Jika Kategori adalah Inverter / Solar PV / Mounting PV, tampilkan filter Brand
    if pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
        if "Brand" in df.columns:
            brand_list = ["Semua Brand"] + list(df["Brand"].dropna().unique())
            pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
            if pilih_brand != "Semua Brand":
                df = df[df["Brand"] == pilih_brand]

    # 4. Filter Pencarian Bebas (Ukuran, Tipe, Spesifikasi)
    search_query = st.sidebar.text_input(
        "Cari Ukuran / Tipe / Spesifikasi:", ""
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
