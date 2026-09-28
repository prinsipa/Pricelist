import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Kabel Supreme", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Kabel Supreme")
st.write(
    "Data harga di bawah ini diambil secara real-time dan otomatis dari Google Spreadsheet."
)


# Fungsi untuk mengambil dan membersihkan data dari semua sheet
@st.cache_data(ttl=60)
def load_all_sheets():
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"
    sheet_names = ["NYM", "NYY", "NYA"]

    all_data = []

    for sheet in sheet_names:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df_temp = pd.read_csv(url)

            # Buang kolom yang tidak ada namanya atau bertuliskan 'Unnamed'
            df_temp = df_temp.loc[
                :, ~df_temp.columns.str.contains("^Unnamed")
            ]

            # Pastikan kolom penting ada
            if "Jenis Kabel" not in df_temp.columns:
                df_temp.insert(0, "Jenis Kabel", sheet)

            all_data.append(df_temp)
        except Exception as e:
            print(f"Gagal memuat sheet {sheet}: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        # Hapus baris yang semuanya kosong
        df_combined = df_combined.dropna(how="all")
        return df_combined
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    # Sidebar Filter Pencarian
    st.sidebar.header("🔍 Filter Pencarian")

    # Filter Jenis Kabel
    if "Jenis Kabel" in df.columns:
        jenis_list = ["Semua Jenis"] + list(df["Jenis Kabel"].dropna().unique())
        pilih_jenis = st.sidebar.selectbox("Pilih Jenis Kabel:", jenis_list)
        if pilih_jenis != "Semua Jenis":
            df = df[df["Jenis Kabel"] == pilih_jenis]

    # Filter Pencarian Fleksibel (Mengabaikan spasi dan huruf besar/kecil)
    search_query = st.sidebar.text_input(
        "Cari Ukuran / Spesifikasi (Contoh: 300):", ""
    )
    if search_query:
        # Ubah semua data dan kata kunci pencarian menjadi huruf kecil dan hilangkan spasi/simbol agar mudah ditemukan
        clean_query = (
            search_query.lower().replace(" ", "").replace("mm2", "").replace("mm²", "")
        )

        def match_row(row):
            row_str = (
                "".join(row.astype(str))
                .lower()
                .replace(" ", "")
                .replace("mm2", "")
                .replace("mm²", "")
            )
            return clean_query in row_str

        df = df[df.apply(match_row, axis=1)]

    # Menampilkan informasi jumlah data dan tabel yang bersih
    st.info(f"Menampilkan {len(df)} data kabel.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Gagal memuat data. Error: {e}")
