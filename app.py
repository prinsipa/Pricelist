import urllib.parse
import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Produk & Material", page_icon="logo.png", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Produk & Material")
st.write(
    "Data harga diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil dan merapikan data per sheet
@st.cache_data(ttl=60)
def load_all_sheets_dict():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # =========================================================================
    # DAFTAR SEMUA TAB / SHEET YANG ADA DI GOOGLE SPREADSHEET
    # (Jika nanti menambah sheet baru, cukup masukkan nama tab-nya di sini)
    # =========================================================================
    sheet_names = [
        "LV Cable (CU)",
        "LV Cable (AL)",
        "MV Cable (CU)",
        "MV Cable (AL)",
        "Inverter",
        "Solar PV",
        "Mounting PV",
        "Baterai",  # Tab baru yang baru saja Anda tambahkan
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
                
                current_core = None
                cleaned_rows = []
                for idx, row in df_temp.iterrows():
                    val = str(row[first_col]).strip()
                    if "CORE" in val.upper() or "core" in val:
                        current_core = val.upper()
                        continue
                    
                    if current_core is None and idx < 5:
                        current_core = "SINGLE CORE"

                    if current_core is not None:
                        row_dict = row.to_dict()
                        row_dict["Kategori Core"] = current_core
                        cleaned_rows.append(row_dict)
                
                if cleaned_rows:
                    df_temp = pd.DataFrame(cleaned_rows)
                else:
                    continue

            # 3. Standarisasi nama kolom pertama kabel menjadi "Ukuran"
            if is_cable and len(df_temp.columns) > 0:
                old_first_col = df_temp.columns[0]
                df_temp = df_temp.rename(columns={old_first_col: "Ukuran"})

            # 4. Buang baris yang kosong total
            df_temp = df_temp.dropna(how="all")

            # 5. Tambahkan informasi kategori berdasarkan nama tab
            if is_cable:
                kategori_nama = "Kabel"
                df_temp["Tipe Kabel"] = sheet
            else:
                kategori_nama = sheet  # Inverter, Solar PV, Mounting PV, Baterai, dll.

            df_temp["Kategori Produk"] = kategori_nama

            data_dict[sheet] = df_temp
        except Exception as e:
            print(f"Gagal memuat sheet '{sheet}': {e}")

    return data_dict


try:
    data_dict = load_all_sheets_dict()

    if not data_dict:
        st.warning("⚠️ Belum ada data yang berhasil dimuat.")
    else:
        all_dfs = list(data_dict.values())
        df_combined = pd.concat(all_dfs, ignore_index=True)
        df_combined.columns = df_combined.columns.str.strip()

        # Sidebar Filter Pencarian Produk
        st.sidebar.header("🔍 Filter Pencarian Produk")

        kategori_options = ["-- Pilih Kategori --"] + list(
            df_combined["Kategori Produk"].dropna().unique()
        )
        pilih_kategori = st.sidebar.selectbox(
            "Pilih Kategori Produk:", kategori_options
        )

        df_active = pd.DataFrame()
        filter_applied = False

        if pilih_kategori != "-- Pilih Kategori --":
            filter_applied = True
            if pilih_kategori == "Kabel":
                cable_sheets = [s for s in data_dict.keys() if "cable" in s.lower() or "kabel" in s.lower()]
                df_active = pd.concat([data_dict[s] for s in cable_sheets if s in data_dict], ignore_index=True)
            else:
                df_active = data_dict.get(pilih_kategori, pd.DataFrame())

            # Filter Sub-Kategori / Brand / Spesifikasi di Sidebar
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
                        filter_applied = True

                if "Kategori Core" in df_active.columns:
                    unique_cores = list(df_active["Kategori Core"].dropna().unique())
                    
                    def core_sort_key(val):
                        if "SINGLE" in val.upper():
                            return (0, val)
                        return (1, val)
                    
                    unique_cores.sort(key=core_sort_key)
                    
                    core_list = ["Semua Core"] + unique_cores
                    pilih_core = st.sidebar.selectbox(
                        "Pilih Jenis Core:", core_list
                    )
                    if pilih_core != "Semua Core":
                        df_active = df_active[df_active["Kategori Core"] == pilih_core]
                        filter_applied = True

                if "Jenis Kabel" in df_active.columns:
                    jenis_list = ["Semua Jenis"] + list(
                        df_active["Jenis Kabel"].dropna().unique()
                    )
                    pilih_jenis = st.sidebar.selectbox(
                        "Pilih Jenis Kabel:", jenis_list
                    )
                    if pilih_jenis != "Semua Jenis":
                        df_active = df_active[df_active["Jenis Kabel"] == pilih_jenis]
                        filter_applied = True

            else:
                # Untuk kategori non-kabel (Inverter, Solar PV, Mounting PV, Baterai, dll.)
                if "Brand" in df_active.columns:
                    brand_list = ["Semua Brand"] + list(
                        df_active["Brand"].dropna().unique()
                    )
                    pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                    if pilih_brand != "Semua Brand":
                        df_active = df_active[df_active["Brand"] == pilih_brand]
                        filter_applied = True

        # Filter Pencarian Bebas
        search_query = st.sidebar.text_input(
            "Cari Ukuran / Tipe / Spesifikasi / Brand:", ""
        )
        if search_query.strip():
            filter_applied = True
            if pilih_kategori == "-- Pilih Kategori --":
                df_active = df_combined.copy()
            
            clean_query = search_query.lower().replace(" ", "")

            def match_row(row):
                row_str = "".join(row.astype(str)).lower().replace(" ", "")
                return clean_query in row_str

            df_active = df_active[df_active.apply(match_row, axis=1)]

        # --- TAMPILAN HALAMAN UTAMA ---
        if not filter_applied or pilih_kategori == "-- Pilih Kategori --":
            st.info("👋 Silakan pilih **Kategori Produk** di sidebar sebelah kiri atau ketik kata kunci pencarian untuk melihat data pricelist.")
        else:
            df_display = df_active.copy()

            cols_to_drop = ["Kategori Produk", "Tipe Kabel"]
            for col in cols_to_drop:
                if col in df_display.columns:
                    df_display = df_display.drop(columns=[col])

            df_display = df_display.loc[:, ~df_display.columns.duplicated()]

            # Bersihkan nilai sel harga yang kosong menjadi tanda strip "-"
            price_cols = ["Harga per Meter (Rp)", "Harga"]
            for p_col in price_cols:
                if p_col in df_display.columns:
                    df_display[p_col] = df_display[p_col].fillna("-").replace(["None", "none", "nan", "NaN", ""], "-")

            # Urutkan kolom khusus kabel agar rapi
            if pilih_kategori == "Kabel":
                preferred_order = ["Ukuran", "Kategori Core", "Jenis Kabel", "Brand", "Spesifikasi", "Harga per Meter (Rp)"]
                existing_cols = [c for c in preferred_order if c in df_display.columns]
                df_display = df_display[existing_cols]

            st.info(f"Menampilkan jumlah produk: {len(df_display)}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Terjadi kesalahan saat memuat data: {e}")
