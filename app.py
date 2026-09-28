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


# Fungsi untuk mengambil data dari Google Spreadsheet secara otomatis
@st.cache_data(ttl=60)  # Data di-refresh otomatis
def load_data():
    # ID Spreadsheet dan GID dari sheet Anda
    spreadsheet_id = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"
    gid = "2016144872"
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    return df


try:
    df = load_data()

    # Kolom Pencarian / Filter di sebelah kiri (Sidebar)
    st.sidebar.header("🔍 Filter Pencarian")
    search_query = st.sidebar.text_input(
        "Cari Ukuran / Spesifikasi Kabel:", ""
    )

    if search_query:
        filtered_df = df[
            df.astype(str)
            .apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        ]
    else:
        filtered_df = df

    # Menampilkan jumlah data dan tabel interaktif
    st.info(f"Menampilkan {len(filtered_df)} data kabel.")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Tombol Refresh Manual
    if st.button("🔄 Muat Ulang Data"):
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(
        f"Gagal memuat data. Pastikan Google Spreadsheet sudah disetel 'Anyone with the link can view'. Error: {e}"
    )
