import urllib.parse
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


# Fungsi untuk mengambil data dari semua sheet secara dinamis
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

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
            encoded_sheet = urllib.parse.quote(sheet)
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
            df_temp = pd.read_csv(url)

            # Buang kolom kosong / Unnamed
            df_temp = df_temp.loc[
                :, ~df_temp.columns.str.contains("^Unnamed")
            ]

            if df_temp.empty:
                continue

            # Bersihkan baris teks pemisah section seperti "SINGLE CORE"
            if "Ukuran" in df_temp.columns:
                df_temp = df_temp.dropna(subset=["Ukuran"])
                df_temp["Ukuran"] = df_temp["Ukuran"].astype(str)
                df_temp = df_temp[
                    ~df_temp["Ukuran"].str.contains("CORE|Core|core", case=False, na=False)
                ]

            # Tentukan Kategori Utama
            sheet_lower = sheet.lower()
            if "cable" in sheet_lower or "kabel" in sheet_lower:
                kategori_nama = "Kabel"
                df_temp.insert(0, "Tipe Kabel", sheet)
            else:
                kategori_nama = sheet  # Inverter, Solar PV, Mounting PV

            df_temp.insert(0, "Kategori Produk", kategori_nama)
            all_data.append(df_temp)
        except Exception as e:
            print(f"Gagal memuat sheet '{sheet}': {e}")

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
        # Sidebar Filter Pencarian Produk
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

        # 2. Filter Sub-Kategori berdasarkan pilihan
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

        elif pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
            if "Brand" in df.columns:
                brand_list = ["Semua Brand"] + list(
                    df["Brand"].dropna().unique()
                )
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df = df[df["Brand"] == pilih_brand]

        # 3. Filter Pencarian Bebas
        search_query = st.sidebar.text_input(
            "Cari Ukuran / Tipe / Spesifikasi:", ""
        )
        if search_query:
            clean_query = search_query.lower().replace(" ", "")

            def match_row(row):
                row_str = "".join(row.astype(str)).lower().replace(" ", "")
                return clean_query in row_str

            df = df[df.apply(match_row, axis=1)]

        # --- PENYESUAIAN TAMPILAN TABEL ---
        # Hapus kolom "Kategori Produk" dari tampilan tabel agar lebih bersih
        if "Kategori Produk" in df.columns:
            df_display = df.drop(columns=["Kategori Produk"])
        else:
            df_display = df.copy()

        # Jika kategori yang dipilih adalah Inverter, Solar PV, atau Mounting PV, susun ulang kolomnya
        if pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
            # Pastikan kolom yang diinginkan ada di dataframe
            desired_cols = [col for col in ["Kategori", "Brand", "Spesifikasi", "Kapasitas", "Harga"] if col in df_display.columns]
            if desired_cols:
                # Jika ada kolom lain yang tersisa, gabungkan
                other_cols = [c for c in df_display.columns if c not in desired_cols]
                df_display = df_display[desired_cols + other_cols]

        # Menampilkan informasi jumlah data dan tabel interaktif yang bersih
        st.info(f"Menampilkan {len(df_display)} data produk.")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
