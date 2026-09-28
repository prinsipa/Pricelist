import io
import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Kabel", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Kabel")
st.write(
    "Data harga diambil secara real-time dari database SharePoint perusahaan."
)


# Fungsi untuk membaca file Excel dari SharePoint / Link Web
@st.cache_data(ttl=60)
def load_excel_from_sharepoint():
    # Masukkan link SharePoint Anda di sini
    # Tips: Ubah parameter di ujung link SharePoint dari '&action=default' menjadi '&download=1'
    sharepoint_url = "https://abirama.sharepoint.com/:x:/r/sites/AbiramaPrinsipaIndonesiaPT/_layouts/15/Doc.aspx?sourcedoc=%7B9562FF9F-78D1-49EF-9E16-E3581F956F10%7D&file=Database%20Pricelist.xlsx&action=default&mobileredirect=true"

    # Mengubah link agar mendownload file Excel secara langsung
    download_url = sharepoint_url.replace("action=default", "download=1")

    # Membaca semua sheet yang ada di dalam file Excel secara otomatis
    excel_file = pd.ExcelFile(download_url)
    sheet_names = excel_file.sheet_names

    all_data = []

    for sheet in sheet_names:
        df_temp = pd.read_excel(excel_file, sheet_name=sheet)

        # Buang kolom yang tidak bernama / Unnamed
        df_temp = df_temp.loc[:, ~df_temp.columns.str.contains("^Unnamed")]

        # Tentukan Kategori Produk berdasarkan nama sheet
        if sheet.lower() in ["nym", "nyy", "nya", "aluminium", "kabel"]:
            kategori_nama = "Kabel"
        else:
            kategori_nama = sheet  # Untuk Inverter, Solar PV, Mounting PV, dll.

        # Tambahkan kolom Kategori di posisi paling depan
        df_temp.insert(0, "Kategori Produk", kategori_nama)

        all_data.append(df_temp)

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined = df_combined.dropna(how="all")
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_excel_from_sharepoint()

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
    st.error(
        f"Gagal memuat data dari SharePoint. Pastikan link dapat diakses publik/organisasi dan file berformat Excel (.xlsx). Error: {e}"
    )
