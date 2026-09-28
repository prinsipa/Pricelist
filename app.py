import pandas as pd
import streamlit as st

# Konfigurasi Tampilan Web
st.set_page_config(
    page_title="Pricelist Kabel Supreme", page_icon="⚡", layout="wide"
)

st.title("⚡ Cek Harga Pricelist Kabel Supreme")
st.write(
    "Data harga di bawah ini diambil secara real-time dan otomatis dari semua sheet Google Spreadsheet."
)


# Fungsi untuk mengambil dan menggabungkan semua sheet sekaligus
@st.cache_data(ttl=60)
def load_all_sheets():
    # Masukkan ID Google Spreadsheet utama Anda
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

    # Daftar nama sheet yang ada di file Google Spreadsheet Anda
    # (Sesuaikan nama sheet ini jika ada tambahan, misal "Aluminium", "N2XY", dll.)
    sheet_names = ["NYM", "NYY", "NYA"]

    all_data = []

    for sheet in sheet_names:
        try:
            # URL export CSV per sheet berdasarkan namanya
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={sheet}"
            df_temp = pd.read_csv(url)
            all_data.append(df_temp)
        except Exception as e:
            print(f"Gagal memuat sheet {sheet}: {e}")

    # Gabungkan semua data sheet menjadi 1 tabel besar
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame()


try:
    df = load_all_sheets()

    # Sidebar Filter Pencarian
    st.sidebar.header("🔍 Filter Pencarian")

    # Filter berdasarkan Jenis Kabel (Dropdown pilihan otomatis dari data)
    if "Jenis Kabel" in df.columns:
        jenis_list = ["Semua Jenis"] + list(df["Jenis Kabel"].dropna().unique())
        pilih_jenis = st.sidebar.selectbox("Pilih Jenis Kabel:", jenis_list)
        if pilih_jenis != "Semua Jenis":
            df = df[df["Jenis Kabel"] == pilih_jenis]

    # Filter pencarian teks bebas (ukuran / spesifikasi)
    search_query = st.sidebar.text_input(
        "Cari Ukuran / Spesifikasi Lainnya:", ""
    )
    if search_query:
        df = df[
            df.astype(str)
            .apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        ]

    # Menampilkan informasi jumlah data dan tabel
    st.info(f"Menampilkan {len(df)} data kabel.")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(
        f"Gagal memuat data. Pastikan Google Spreadsheet sudah disetel 'Anyone with the link can view'. Error: {e}"
    )
