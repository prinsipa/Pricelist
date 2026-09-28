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


# Fungsi untuk mengambil data dari semua sheet secara terpisah ke dalam dictionary
@st.cache_data(ttl=60)
def load_all_sheets_dict():
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
    data_dict = {}

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
            
            # Simpan per sheet ke dictionary
            data_dict[sheet] = df_temp
        except Exception as e:
            print(f"Gagal memuat sheet '{sheet}': {e}")

    return data_dict


try:
    data_dict = load_all_sheets_dict()

    if not data_dict:
        st.warning("⚠️ Belum ada data yang berhasil dimuat.")
    else:
        # Gabungkan semua data untuk list dropdown filter
        all_dfs = list(data_dict.values())
        df_combined = pd.concat(all_dfs, ignore_index=True)

        # Sidebar Filter Pencarian Produk
        st.sidebar.header("🔍 Filter Pencarian Produk")

        # 1. Filter Kategori Produk Utama
        kategori_list = ["Semua Kategori"] + list(
            df_combined["Kategori Produk"].dropna().unique()
        )
        pilih_kategori = st.sidebar.selectbox(
            "Pilih Kategori Produk:", kategori_list
        )

        # Tentukan dataframe aktif berdasarkan pilihan kategori
        if pilih_kategori == "Semua Kategori":
            df_active = df_combined.copy()
        elif pilih_kategori == "Kabel":
            cable_sheets = [s for s in data_dict.keys() if "cable" in s.lower() or "kabel" in s.lower()]
            df_active = pd.concat([data_dict[s] for s in cable_sheets if s in data_dict], ignore_index=True)
        else:
            # Untuk Inverter, Solar PV, Mounting PV
            df_active = data_dict.get(pilih_kategori, pd.DataFrame())

        # 2. Filter Sub-Kategori / Brand
        if pilih_kategori == "Kabel":
            if "Tipe Kabel" in df_active.columns:
                tipe_list = ["Semua Spesifikasi"] + list(
                    df_active["Tipe Kabel"].dropna().unique()
                )
                pilih_tipe = st.sidebar.selectbox(
                    "Pilih Spesifikasi Kabel:", tipe_list
                )
                if pilih_tipe != "Semua Spesifikasi":
                    df_active = df_active[df_active["Tipe Kabel"] == pilih_tipe]

            if "Jenis Kabel" in df_active.columns:
                jenis_list = ["Semua Jenis"] + list(
                    df_active["Jenis Kabel"].dropna().unique()
                )
                pilih_jenis = st.sidebar.selectbox(
                    "Pilih Jenis Kabel:", jenis_list
                )
                if pilih_jenis != "Semua Jenis":
                    df_active = df_active[df_active["Jenis Kabel"] == pilih_jenis]

        elif pilih_kategori in ["Inverter", "Solar PV", "Mounting PV"]:
            if "Brand" in df_active.columns:
                brand_list = ["Semua Brand"] + list(
                    df_active["Brand"].dropna().unique()
                )
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df_active = df_active[df_active["Brand"] == pilih_brand]

        # 3. Filter Pencarian Bebas
        search_query = st.sidebar.text_input(
            "Cari Ukuran / Tipe / Spesifikasi / Brand:", ""
        )
        if search_query:
            clean_query = search_query.lower().replace(" ", "")

            def match_row(row):
                row_str = "".join(row.astype(str)).lower().replace(" ", "")
                return clean_query in row_str

            df_active = df_active[df_active.apply(match_row, axis=1)]

        # --- BERSIHKAN KOLOM TAMPILAN ---
        # Hapus kolom "Kategori Produk" agar tidak berulang
        if "Kategori Produk" in df_active.columns:
            df_display = df_active.drop(columns=["Kategori Produk"])
        else:
            df_display = df_active.copy()

        # Buang kolom yang seluruh isinya kosong atau bernilai NaN / 'None'
        df_display = df_display.dropna(how="all", axis=1)
        df_display = df_display.loc[:, ~df_display.isin(["None", "none", "nan", "NaN"]).all()]

        # Menampilkan informasi jumlah data dan tabel interaktif yang bersih tanpa kolom kosong
        st.info(f"Menampilkan {len(df_display)} data produk.")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
