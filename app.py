import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Material", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Material")
st.write(
    "Data harga diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil data dari semua sheet secara otomatis
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Daftar nama tab yang ingin dibaca (pastikan sama persis dengan di Google Spreadsheet Anda)
    sheet_names = [
        "LV Cable (CU)",
        "LV Cable (AL)",
        "MV Cable (CU)",
        "MV Cable (AL)",
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

            if df_temp.empty:
                continue

            # Bersihkan baris teks header section seperti "SINGLE CORE", "2 CORE", dll.
            if "Ukuran" in df_temp.columns:
                df_temp = df_temp.dropna(subset=["Ukuran"])
                df_temp["Ukuran"] = df_temp["Ukuran"].astype(str)
                df_temp = df_temp[
                    ~df_temp["Ukuran"].str.contains("CORE|Core|core", case=False, na=False)
                ]

            # Tentukan Kategori Utama berdasarkan nama tab
            sheet_lower = sheet.lower()
            if "cable" in sheet_lower or "kabel" in sheet_lower:
                kategori_nama = "Kabel"
                df_temp.insert(0, "Tipe Kabel", sheet)
            else:
                kategori_nama = sheet  # Inverter, Solar PV, Mounting PV

            # Tambahkan kolom Kategori Produk di posisi paling depan
            df_temp.insert(0, "Kategori Produk", kategori_nama)

            all_data.append(df_temp)
        except Exception as e:
            # Cetak error ke console untuk debugging jika ada tab yang gagal
            print(f"Catatan: Gagal memuat sheet '{sheet}': {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    if df.empty:
        st.warning(
            "⚠️ Belum ada data yang berhasil dimuat. Pastikan nama tab di Google Spreadsheet Anda sudah sesuai."
        )
    else:
        # Sidebar Filter Pencarian Produk
        st.sidebar.header("🔍 Filter Pencarian Produk")

        # 1. Filter Kategori Produk Utama (Otomatis mendeteksi semua kategori unik dari data)
        if "Kategori Produk" in df.columns:
            kategori_list = ["Semua Kategori"] + list(
                df["Kategori Produk"].dropna().unique()
            )
            pilih_kategori = st.sidebar.selectbox(
                "Pilih Kategori Produk:", kategori_list
            )
            if pilih_kategori != "Semua Kategori":
                df = df[df["Kategori Produk"] == pilih_kategori]

        # 2. Jika Kategori adalah KABEL, tampilkan sub-filter Spesifikasi Kabel & Jenis Kabel
        if pilih_kategori == "Kabel":
            if "Tipe Kabel" in df.columns:
                tipe_list = ["Semua Spesifikasi"] + list(
                    df["Tipe Kabel"].dropna().unique()
                )
                pilih_tipe = st.sidebar.selectbox(
                    "Pilih Spesifikasi Kabel:", tipe_list
                )
                if pilih_tipe != "Semua Spesifikasi":
                    df = df[df["Tipe Kabel"] == pilih_tipe]

            if "Jenis Kabel" in df.columns:
                jenis_list = ["Semua Jenis"] + list(
                    df["Jenis Kabel"].dropna().unique()
                )
                pilih_jenis = st.sidebar.selectbox(
                    "Pilih Jenis Kabel:", jenis_list
                )
                if pilih_jenis != "Semua Jenis":
                    df = df[df["Jenis Kabel"] == pilih_jenis]

        # 3. Jika Kategori adalah Inverter / Solar PV / Mounting PV, tampilkan filter Brand
        elif pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
            if "Brand" in df.columns:
                brand_list = ["Semua Brand"] + list(
                    df["Brand"].dropna().unique()
                )
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df = df[df["Brand"] == pilih_brand]
        
        # Jika memilih "Semua Kategori", tampilkan opsi tambahan jika diperlukan
        elif pilih_kategori == "Semua Kategori":
            if "Brand" in df.columns and st.sidebar.checkbox("Filter Berdasarkan Brand"):
                brand_list = ["Semua Brand"] + list(df["Brand"].dropna().unique())
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df = df[df["Brand"] == pilih_brand]

        # 4. Filter Pencarian Bebas (Ukuran / Tipe / Spesifikasi)
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
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
