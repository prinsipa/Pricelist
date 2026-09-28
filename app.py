import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Kabel", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Material")
st.write(
    "Data harga diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil data dari semua sheet secara dinamis
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Daftar nama tab/sheet sesuai dengan Google Spreadsheet Anda
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

            # Bersihkan baris pemisah kategori core (misal: "SINGLE CORE", "2 CORE", dll.)
            # Baris pemisah biasanya hanya terisi teks di kolom pertama dan kolom lainnya kosong/NaN
            if "Ukuran" in df_temp.columns:
                # Jika ada baris yang bertuliskan CORE, kita bisa jadikan itu sebagai informasi tambahan atau dibersihkan
                df_temp = df_temp.dropna(
                    subset=["Harga per Meter (Rp)", "Ukuran"], how="all"
                )

            # Tentukan Kategori Utama berdasarkan nama sheet
            if "Cable" in sheet:
                kategori_nama = "Kabel"
                # Tentukan jenis konduktor dan tegangan dari nama sheet
                df_temp.insert(
                    0, "Tipe Kabel", sheet
                )  # Contoh: LV Cable (CU), MV Cable (AL)
            else:
                kategori_nama = (
                    sheet  # Untuk Inverter, Solar PV, Mounting PV, dll.
                )

            # Tambahkan kolom Kategori Produk di posisi paling depan
            df_temp.insert(0, "Kategori Produk", kategori_nama)

            all_data.append(df_temp)
        except Exception as e:
            print(f"Gagal memuat sheet {sheet}: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    if df.empty:
        st.warning("⚠️ Belum ada data yang berhasil dimuat.")
    else:
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

        # 2. Jika Kategori adalah Kabel, tampilkan sub-filter berdasarkan Tipe/Tab Kabel
        if pilih_kategori == "Kabel" or pilih_kategori == "Semua Kategori":
            if "Tipe Kabel" in df.columns:
                tipe_kabel_list = ["Semua"] + list(
                    df["Tipe Kabel"].dropna().unique()
                )
                pilih_tipe_kabel = st.sidebar.selectbox(
                    "Pilih Spesifikasi Kabel (LV/MV & CU/AL):", tipe_kabel_list
                )
                if pilih_tipe_kabel != "Semua":
                    df = df[df["Tipe Kabel"] == pilih_tipe_kabel]

            if "Jenis Kabel" in df.columns:
                jenis_kabel_list = ["Semua"] + list(
                    df["Jenis Kabel"].dropna().unique()
                )
                pilih_jenis_kabel = st.sidebar.selectbox(
                    "Pilih Jenis Kabel (NYM/NYY/NYA):", jenis_kabel_list
                )
                if pilih_jenis_kabel != "Semua":
                    df = df[df["Jenis Kabel"] == pilih_jenis_kabel]

        # 3. Jika Kategori adalah Inverter / Solar PV / Mounting PV, tampilkan filter Brand
        if pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
            if "Brand" in df.columns:
                brand_list = ["Semua Brand"] + list(
                    df["Brand"].dropna().unique()
                )
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df = df[df["Brand"] == pilih_brand]

        # 4. Filter Pencarian Bebas
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
