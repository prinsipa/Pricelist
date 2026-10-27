import io
import os
import re
import urllib.parse

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Konfigurasi halaman (harus menjadi perintah Streamlit pertama)
# ---------------------------------------------------------------------------
# Kalau logo.png tidak ada di repo, pakai emoji supaya app tidak error.
PAGE_ICON = "logo.png" if os.path.exists("logo.png") else "📊"

st.set_page_config(
    page_title="Pricelist Product & Material", page_icon=PAGE_ICON, layout="wide"
)

st.title("Pricelist Produk & Material")
st.write("Data harga diambil secara real-time dan otomatis dari Google Spreadsheet.")

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
SPREADSHEET_ID = "1b4NV7g90Aj8eMS6M4OwLuvzOb273_LOjctKMEqZg3k4"

SHEET_NAMES = [
    "LV Cable (CU)",
    "LV Cable (AL)",
    "MV Cable (CU)",
    "MV Cable (AL)",
    "DC Cable",
    "Inverter",
    "Solar PV",
    "Mounting PV",
    "Baterai",
    "Transformer",
]

DEFAULT_CAT = "-- Pilih Kategori --"
CACHE_TTL = 300  # detik; lebih jarang menembak Google supaya tidak kena rate limit

# Judul section pada sheet kabel, mis. "SINGLE CORE", "2 CORE", "3 CORE", "4 CORE"
CORE_PATTERN = re.compile(r"^\s*(SINGLE|\d+)\s*CORE\b", re.IGNORECASE)

EMPTY_MARKERS = ["None", "none", "nan", "NaN", ""]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def is_cable_name(name: str) -> bool:
    n = name.lower()
    return "cable" in n or "kabel" in n


def show_dataframe(df: pd.DataFrame):
    """Kompatibel dengan versi Streamlit lama maupun baru."""
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True)


def add_cable_core_column(df: pd.DataFrame) -> pd.DataFrame:
    """Ubah baris judul section (SINGLE CORE, 2 CORE, ...) menjadi kolom 'Kategori Core'."""
    first_col = df.columns[0]
    first_vals = df[first_col].astype(str)

    is_section = first_vals.str.match(CORE_PATTERN)
    core_label = first_vals.where(is_section).str.strip().str.upper()
    core_label = core_label.ffill().fillna("SINGLE CORE")

    df = df.assign(**{"Kategori Core": core_label})
    df = df[~is_section].copy()
    return df.rename(columns={first_col: "Ukuran"})


# ---------------------------------------------------------------------------
# Pengambilan data (per sheet di-cache; sheet yang gagal TIDAK ikut di-cache)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_sheet(sheet: str) -> pd.DataFrame:
    encoded = urllib.parse.quote(sheet)
    url = (
        f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={encoded}"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))

    # Rapikan nama kolom, buang kolom Unnamed dan baris kosong
    df.columns = df.columns.astype(str).str.strip()
    df = df.loc[:, ~df.columns.str.contains("^Unnamed", case=False)]
    df = df.dropna(how="all")
    if df.empty or len(df.columns) == 0:
        return pd.DataFrame()

    if is_cable_name(sheet):
        df = add_cable_core_column(df)
        if df.empty:
            return pd.DataFrame()
        df["Tipe Kabel"] = sheet
        df["Kategori Produk"] = "Kabel"
    else:
        df["Kategori Produk"] = sheet

    # Kolom pencarian dibuat SEKALI di sini, bukan di setiap pencarian
    df["_search"] = (
        df.fillna("")
        .astype(str)
        .agg("".join, axis=1)
        .str.lower()
        .str.replace(r"[^a-z0-9]", "", regex=True)
    )
    return df.reset_index(drop=True)


def load_all_sheets():
    data, errors = {}, {}
    for sheet in SHEET_NAMES:
        try:
            df = load_sheet(sheet)
            if not df.empty:
                data[sheet] = df
        except Exception as e:  # noqa: BLE001
            errors[sheet] = str(e)
    return data, errors


# ---------------------------------------------------------------------------
# Callback widget (hanya memakai key widget sebagai satu-satunya sumber state)
# ---------------------------------------------------------------------------
def on_change_search():
    if st.session_state.widget_search.strip():
        st.session_state.widget_cat = DEFAULT_CAT


def on_change_category():
    if st.session_state.widget_cat != DEFAULT_CAT:
        st.session_state.widget_search = ""


# ---------------------------------------------------------------------------
# Aplikasi utama
# ---------------------------------------------------------------------------
def main():
    with st.spinner("Memuat data..."):
        data_dict, errors = load_all_sheets()

    # Tampilkan sheet yang gagal dimuat, jangan hilang diam-diam
    if errors:
        with st.expander(f"⚠️ {len(errors)} sheet gagal dimuat", expanded=False):
            for name, msg in errors.items():
                st.write(f"**{name}**: {msg}")

    if not data_dict:
        st.warning("⚠️ Belum ada data yang berhasil dimuat. Coba klik 'Muat Ulang Data'.")
        return

    cable_sheets = [s for s in data_dict if is_cable_name(s)]
    non_cable_cats = [s for s in data_dict if not is_cable_name(s)]

    df_all_master = pd.concat(data_dict.values(), ignore_index=True)
    df_cable_combined = (
        pd.concat([data_dict[s] for s in cable_sheets], ignore_index=True)
        if cable_sheets
        else pd.DataFrame()
    )

    kategori_options = [DEFAULT_CAT]
    if cable_sheets:
        kategori_options.append("Kabel")
    kategori_options += non_cable_cats

    # Nilai awal widget
    st.session_state.setdefault("widget_search", "")
    st.session_state.setdefault("widget_cat", DEFAULT_CAT)
    if st.session_state.widget_cat not in kategori_options:
        st.session_state.widget_cat = DEFAULT_CAT

    # Sidebar
    st.sidebar.header("🔍 Filter Pencarian Produk")
    st.sidebar.text_input(
        "Cari Bebas (Ukuran / Tipe / Spesifikasi / Brand):",
        key="widget_search",
        on_change=on_change_search,
    )
    st.sidebar.selectbox(
        "Pilih Kategori Produk:",
        kategori_options,
        key="widget_cat",
        on_change=on_change_category,
    )

    search_text = st.session_state.widget_search.strip()
    active_cat = st.session_state.widget_cat

    df_active = pd.DataFrame()

    # --- Mode 1: pencarian bebas ---
    if search_text:
        clean_search = re.sub(r"[^a-z0-9]", "", search_text.lower())
        if not clean_search:
            st.warning("Kata kunci tidak valid. Gunakan huruf atau angka.")
            return
        mask = df_all_master["_search"].str.contains(clean_search, na=False, regex=False)
        df_active = df_all_master[mask]

    # --- Mode 2: pilih kategori ---
    elif active_cat != DEFAULT_CAT:
        if active_cat == "Kabel":
            df_active = df_cable_combined.copy()

            if "Tipe Kabel" in df_active.columns:
                tipe_list = ["Semua Spesifikasi"] + list(df_active["Tipe Kabel"].dropna().unique())
                pilih_tipe = st.sidebar.selectbox("Pilih Spesifikasi Kabel:", tipe_list)
                if pilih_tipe != "Semua Spesifikasi":
                    df_active = df_active[df_active["Tipe Kabel"] == pilih_tipe]

            if "Kategori Core" in df_active.columns:
                cores = sorted(
                    df_active["Kategori Core"].dropna().unique(),
                    key=lambda v: (0 if "SINGLE" in v.upper() else 1, v),
                )
                pilih_core = st.sidebar.selectbox("Pilih Jenis Core:", ["Semua Core"] + cores)
                if pilih_core != "Semua Core":
                    df_active = df_active[df_active["Kategori Core"] == pilih_core]

            if "Jenis Kabel" in df_active.columns:
                jenis_list = ["Semua Jenis"] + list(df_active["Jenis Kabel"].dropna().unique())
                pilih_jenis = st.sidebar.selectbox("Pilih Jenis Kabel:", jenis_list)
                if pilih_jenis != "Semua Jenis":
                    df_active = df_active[df_active["Jenis Kabel"] == pilih_jenis]
        else:
            df_active = data_dict.get(active_cat, pd.DataFrame())
            if "Brand" in df_active.columns:
                brand_list = ["Semua Brand"] + list(df_active["Brand"].dropna().unique())
                pilih_brand = st.sidebar.selectbox("Pilih Brand:", brand_list)
                if pilih_brand != "Semua Brand":
                    df_active = df_active[df_active["Brand"] == pilih_brand]

    # --- Belum ada filter ---
    else:
        st.info(
            "👋 Silakan pilih **Kategori Produk** di sidebar sebelah kiri "
            "atau ketik kata kunci pencarian untuk melihat data pricelist."
        )
        return

    # --- Tampilan hasil ---
    if df_active.empty:
        st.warning("Tidak ada produk yang cocok dengan filter/pencarian Anda.")
        return

    for cat in df_active["Kategori Produk"].dropna().unique():
        df_display = df_active[df_active["Kategori Produk"] == cat].copy()
        if df_display.empty:
            continue

        st.subheader(f"📂 Kategori: {cat}")

        df_display = df_display.drop(
            columns=[c for c in ["Kategori Produk", "Tipe Kabel", "_search"] if c in df_display.columns]
        )
        df_display = df_display.loc[:, ~df_display.columns.duplicated()]

        # Harga kosong -> "-"
        for p_col in ["Harga per Meter (Rp)", "Harga"]:
            if p_col in df_display.columns:
                df_display[p_col] = df_display[p_col].fillna("-").replace(EMPTY_MARKERS, "-")

        # Buang kolom yang kosong total
        df_display = df_display.dropna(how="all", axis=1)
        df_display = df_display.loc[:, ~df_display.isin(EMPTY_MARKERS + ["-"]).all()]

        # Urutan kolom
        if cat == "Kabel":
            preferred = ["Ukuran", "Kategori Core", "Jenis Kabel", "Brand", "Spesifikasi", "Harga per Meter (Rp)"]
            df_display = df_display[[c for c in preferred if c in df_display.columns]]
        else:
            preferred = ["Kapasitas", "Brand", "Spesifikasi", "Harga"]
            first = [c for c in preferred if c in df_display.columns]
            rest = [c for c in df_display.columns if c not in first]
            df_display = df_display[first + rest]

        st.info(f"Menampilkan jumlah produk ({cat}): {len(df_display)}")
        show_dataframe(df_display)


try:
    main()
except Exception as e:  # noqa: BLE001
    st.error(f"Terjadi kesalahan saat memuat data: {e}")

# Tombol muat ulang berada DI LUAR try/main, jadi selalu muncul meski terjadi error
if st.sidebar.button("🔄 Muat Ulang Data"):
    st.cache_data.clear()
    st.rerun()
