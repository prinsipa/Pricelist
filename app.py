import urllib.parse
import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Material", page_icon="⚡", layout="wide"
)

st.title("Pricelist Produk & Material")
st.write(
    "Data harga diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil dan merapikan data per sheet
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

            # 1. Bersihkan nama kolom dari spasi tersembunyi
            df_temp.columns = df_temp.columns.str.strip()

            # 2. Buang kolom kosong atau Unnamed
            df_temp = df_temp.loc[:, ~df_temp.columns.str.contains("^Unnamed", case=False)]

            if df_temp.empty:
                continue

            # Jika ini adalah sheet kabel, tangkap baris section (SINGLE CORE, 2 CORE, dll)
            sheet_lower = sheet.lower()
            is_cable = "cable" in sheet_lower or "kabel" in sheet_lower

            if is_cable and len(df_temp.columns) > 0:
                first_col = df_temp.columns[0]
                
                # Buat kolom penanda Core baru berdasarkan baris pemisah di spreadsheet
                current_core = "Standard"
                core_list = []
                
                cleaned_rows = []
                for idx, row in df_temp.iterrows():
                    val = str(row[first_col]).strip()
                    # Cek apakah baris ini adalah baris pemisah core (misal mengandung kata CORE)
                    if "CORE" in val.upper() or "core" in val:
                        current_core = val.upper()  # Contoh: SINGLE CORE, 2 CORE, dll.
                        continue  # Lewati baris pemisah ini agar tidak jadi data produk
                    
                    # Jika bukan baris pemisah, catat core-nya dan simpan barisnya
                    row_dict = row.to_dict()
                    row_dict["Kategori Core"] = current_core
                    cleaned_rows.append(row_dict)
                
                if cleaned_rows:
                    df_temp = pd.DataFrame(cleaned_rows)
                else:
                    continue

            # 3. Standarisasi nama kolom pertama kabel menjadi "Ukuran"
            if is_cable and len(df_temp.columns) > 0:
                # Ganti nama kolom pertama apa pun itu (termasuk "Ukuran SINGLE CORE") menjadi "Ukuran"
                old_first_col = df_temp.columns[0]
                df_temp = df_temp.rename(columns={old_first_col: "Ukuran"})

            # 4. Buang baris yang kosong total
            df_temp = df_temp.dropna(how="all")

            # 5. Tambahkan informasi kategori berdasarkan nama tab
            if is_cable:
                kategori_nama = "Kabel"
                df_temp["Tipe Kabel"] = sheet
            else:
                kategori_nama = sheet  # Inverter, Solar PV, Mounting PV

            df_temp["Kategori Produk"] = kategori_nama

            # Simpan dataframe bersih ke dictionary
            data_dict[sheet] = df_temp
        except Exception as e:
            print(f"Gagal memuat sheet '{sheet}': {e}")

    return data_dict


try:
    data_dict = load_all_sheets_dict()

    if not data_dict:
        st.warning("⚠️ Belum ada data yang berhasil dimuat.")
    else:
        # Gabungkan semua data untuk filter utama
        all_dfs = list(data_dict.values())
        df_combined = pd.concat(all_dfs, ignore_index=True)
        df_combined.columns = df_combined.columns.str.strip()

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
            df_active = data_dict.get(pilih_kategori, pd.DataFrame())

        # 2. Filter Sub-Kategori / Brand di Sidebar
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

            # Tambahan filter pilihan Core (Single Core, 2 Core, dll) di sidebar agar makin rapi
            if "Kategori Core" in df_active.columns:
                core_list = ["Semua Core"] + list(
                    df_active["Kategori Core"].dropna().unique()
                )
                pilih_core = st.sidebar.selectbox(
                    "Pilih Jenis Core:", core_list
                )
                if pilih_core != "Semua Core":
                    df_active = df_active[df_active["Kategori Core"] == pilih_core]

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

        # --- BERSIHKAN TAMPILAN TABEL MUTLAK ---
        df_display = df_active.copy()

        # Hapus kolom helper sistem agar tidak tampil di web
        cols_to_drop = ["Kategori Produk", "Tipe Kabel"]
        for col in cols_to_drop:
            if col in df_display.columns:
                df_display = df_display.drop(columns=[col])

        # Buang kolom yang namanya duplikat
        df_display = df_display.loc[:, ~df_display.columns.duplicated()]

        # Hapus kolom apa pun yang seluruh isinya 'None' atau kosong
        df_display = df_display.dropna(how="all", axis=1)
        df_display = df_display.loc[:, ~df_display.isin(["None", "none", "nan", "NaN", ""]).all()]

        # Urutkan kolom khusus kabel agar rapi: Ukuran, Kategori Core, Jenis Kabel, Brand, Spesifikasi, Harga per Meter (Rp)
        if pilih_kategori == "Kabel" or pilih_kategori == "Semua Kategori":
            preferred_order = ["Ukuran", "Kategori Core", "Jenis Kabel", "Brand", "Spesifikasi", "Harga per Meter (Rp)"]
            existing_cols = [c for c in preferred_order if c in df_display.columns]
            other_cols = [c for c in df_display.columns if c not in existing_cols]
            df_display = df_display[existing_cols + other_cols]

        # Menampilkan informasi jumlah produk dan tabel interaktif yang bersih
        st.info(f"Menampilkan jumlah produk: {len(df_display)}")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
