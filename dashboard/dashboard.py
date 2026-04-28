import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Air Quality Dashboard – Dongsi vs Dingling",
    page_icon="🌫️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 5px solid #C0392B;
    }
    .metric-card.blue { border-left-color: #2E86C1; }
    h1 { color: #2C3E50; }
    </style>
    """,
    unsafe_allow_html=True,
)

PALETTE = {"Dongsi": "#C0392B", "Dingling": "#2E86C1"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    """Load and clean a single air-quality CSV file.
    Path dicari relatif terhadap lokasi dashboard.py bukan terminal."""
    if not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(filepath):
        return pd.DataFrame()

    df = pd.read_csv(filepath)

    # Drop auto-index column if present
    if "No" in df.columns:
        df.drop("No", axis=1, inplace=True)

    # Interpolate numeric missing values
    num_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[num_cols] = df[num_cols].interpolate(method="linear")

    # Forward-fill wind direction
    if "wd" in df.columns:
        df["wd"].fillna(method="ffill", inplace=True)

    # Build datetime column
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])

    # Season label
    def season(m):
        if m in [12, 1, 2]:
            return "Winter"
        elif m in [3, 4, 5]:
            return "Spring"
        elif m in [6, 7, 8]:
            return "Summer"
        return "Autumn"

    df["season"] = df["month"].apply(season)
    return df

with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Flag_of_the_People%27s_Republic_of_China.svg/320px-Flag_of_the_People%27s_Republic_of_China.svg.png",
        width=80,
    )
    st.title("⚙️ Pengaturan")

    data_dir = st.text_input("Path File CSV", value="main_data.csv")
    df_raw = load_data(data_dir)

    if df_raw.empty:
        st.error(
            "❌ File tidak ditemukan.\n\n"
            "Pastikan path mengarah ke file CSV yang benar.\n\n"
            "Contoh: `main_data/main_data.csv`"
        )
        st.stop()

    stations = sorted(df_raw["station"].unique().tolist())
    selected_stations = st.multiselect("Pilih Stasiun", stations, default=stations)

    year_min = int(df_raw["year"].min())
    year_max = int(df_raw["year"].max())
    year_range = st.slider("Rentang Tahun", year_min, year_max, (year_min, year_max))

    st.markdown("---")
    st.caption("Proyek Analisis Data – Air Quality Dataset\n\n**Henokh William Christianos Lase**")

df = df_raw[
    df_raw["station"].isin(selected_stations)
    & df_raw["year"].between(year_range[0], year_range[1])
].copy()

if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

st.title("🌫️ Dashboard Kualitas Udara – Beijing")
st.markdown(
    "Perbandingan **PM2.5** antara wilayah urban **Dongsi** dan pinggiran **Dingling** (2013–2017)"
)
st.markdown("---")

kpi_cols = st.columns(len(selected_stations) * 2)
col_idx = 0
for station in selected_stations:
    subset = df[df["station"] == station]["PM2.5"]
    color = "red" if station == "Dongsi" else "blue"
    with kpi_cols[col_idx]:
        st.metric(
            label=f"📍 {station} – Rata-rata PM2.5",
            value=f"{subset.mean():.1f} µg/m³",
            delta=f"Max {subset.max():.0f} µg/m³",
        )
    col_idx += 1
    with kpi_cols[col_idx]:
        bad_pct = (subset > 75).mean() * 100
        st.metric(
            label=f"⚠️ {station} – % Hari Tidak Sehat (>75)",
            value=f"{bad_pct:.1f}%",
        )
    col_idx += 1

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Tren Bulanan", "🌸 Pola Musiman", "🔬 EDA & Korelasi", "📊 Analisis RFM"]
)

with tab1:
    st.subheader("Tren Rata-rata PM2.5 Bulanan")
    st.caption(
        "Pertanyaan 1: Bagaimana pola fluktuasi PM2.5 bulanan antara Dongsi (urban) dan Dingling (pinggiran)?"
    )

    trend_df = (
        df.groupby(["year", "month", "station"])["PM2.5"].mean().reset_index()
    )
    trend_df["period"] = (
        trend_df["year"].astype(str)
        + "-"
        + trend_df["month"].astype(str).str.zfill(2)
    )
    trend_df.sort_values("period", inplace=True)

    fig, ax = plt.subplots(figsize=(14, 5))
    for station in selected_stations:
        sub = trend_df[trend_df["station"] == station]
        ax.plot(sub["period"], sub["PM2.5"], label=station, color=PALETTE.get(station), linewidth=2)
        ax.fill_between(sub["period"], sub["PM2.5"], alpha=0.1, color=PALETTE.get(station))

    ax.axhline(75, color="orange", linestyle="--", linewidth=1.2, label="Batas Sehat (75 µg/m³)")
    step = max(1, len(trend_df["period"].unique()) // 8)
    ticks = trend_df["period"].unique()[::step]
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticks, rotation=45, ha="right")
    ax.set_xlabel("Tahun-Bulan")
    ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
    ax.set_title("Tren Konsentrasi PM2.5 per Bulan")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    with st.expander("📌 Insight"):
        st.markdown(
            """
- Terlihat pola fluktuasi tahunan yang konsisten – **puncak polusi di Desember–Februari**, terendah Juni–Agustus.
- **Dongsi** (urban) secara konsisten lebih tinggi dari **Dingling** (pinggiran), tetapi keduanya bergerak searah.
- Garis oranye menunjukkan batas sehat WHO – sering terlewati terutama di musim dingin.
"""
        )

with tab2:
    st.subheader("Tingkat Polusi PM2.5 Berdasarkan Musim")
    st.caption(
        "Pertanyaan 2: Apakah musim berpengaruh terhadap PM2.5 di kedua wilayah?"
    )

    col_a, col_b = st.columns(2)

    with col_a:
        fig2, ax2 = plt.subplots(figsize=(7, 5))
        season_order = ["Spring", "Summer", "Autumn", "Winter"]
        palette_list = [PALETTE.get(s, "#888") for s in selected_stations]
        sns.barplot(
            data=df[df["station"].isin(selected_stations)],
            x="season",
            y="PM2.5",
            hue="station",
            order=season_order,
            palette={s: PALETTE.get(s, "#888") for s in selected_stations},
            ax=ax2,
        )
        ax2.axhline(75, color="orange", linestyle="--", linewidth=1, label="Batas Sehat")
        ax2.set_title("Rata-rata PM2.5 per Musim")
        ax2.set_ylabel("PM2.5 (µg/m³)")
        ax2.set_xlabel("Musim")
        ax2.legend()
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()

    with col_b:
        fig3, ax3 = plt.subplots(figsize=(7, 5))
        df_pivot = (
            df[df["station"].isin(selected_stations)]
            .groupby(["season", "station"])["PM2.5"]
            .mean()
            .unstack()
            .reindex(season_order)
        )
        df_pivot.plot(kind="line", marker="o", ax=ax3, color=[PALETTE.get(s, "#888") for s in df_pivot.columns])
        ax3.axhline(75, color="orange", linestyle="--", linewidth=1, label="Batas Sehat")
        ax3.set_title("Tren Musiman PM2.5")
        ax3.set_ylabel("PM2.5 (µg/m³)")
        ax3.set_xlabel("Musim")
        ax3.legend()
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()

    with st.expander("📌 Insight"):
        st.markdown(
            """
- **Musim Dingin (Winter)** → polusi tertinggi; diduga akibat pemanas & inversi suhu.
- **Musim Panas (Summer)** → polusi terendah; curah hujan membantu pembersihan udara.
- Polusi bersifat **regional** – bahkan Dingling (pinggiran) mengalami lonjakan tajam di winter.
"""
        )

with tab3:
    st.subheader("Eksplorasi Data & Korelasi Meteorologi")

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Distribusi PM2.5 per Stasiun**")
        fig4, ax4 = plt.subplots(figsize=(6, 4))
        for station in selected_stations:
            sub = df[df["station"] == station]["PM2.5"].dropna()
            ax4.hist(sub, bins=50, alpha=0.55, label=station, color=PALETTE.get(station))
        ax4.axvline(75, color="orange", linestyle="--", linewidth=1, label="Batas Sehat")
        ax4.set_xlabel("PM2.5 (µg/m³)")
        ax4.set_ylabel("Frekuensi")
        ax4.set_title("Histogram PM2.5")
        ax4.legend()
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

    with col_d:
        st.markdown("**Box Plot PM2.5 per Stasiun**")
        fig5, ax5 = plt.subplots(figsize=(6, 4))
        box_data = [
            df[df["station"] == s]["PM2.5"].dropna().values
            for s in selected_stations
        ]
        bp = ax5.boxplot(box_data, labels=selected_stations, patch_artist=True)
        for patch, station in zip(bp["boxes"], selected_stations):
            patch.set_facecolor(PALETTE.get(station, "#888"))
        ax5.axhline(75, color="orange", linestyle="--", linewidth=1, label="Batas Sehat")
        ax5.set_ylabel("PM2.5 (µg/m³)")
        ax5.set_title("Boxplot PM2.5")
        ax5.legend()
        plt.tight_layout()
        st.pyplot(fig5)
        plt.close()

    st.markdown("**Korelasi Antar Variabel Meteorologi**")
    corr_cols = ["PM2.5", "TEMP", "PRES", "DEWP", "WSPM"]
    avail_cols = [c for c in corr_cols if c in df.columns]

    corr_tab_cols = st.columns(len(selected_stations))
    for i, station in enumerate(selected_stations):
        with corr_tab_cols[i]:
            st.caption(f"**{station}**")
            corr_matrix = df[df["station"] == station][avail_cols].corr()
            fig6, ax6 = plt.subplots(figsize=(5, 4))
            sns.heatmap(
                corr_matrix,
                annot=True,
                fmt=".2f",
                cmap="coolwarm",
                center=0,
                ax=ax6,
                linewidths=0.5,
            )
            ax6.set_title(f"Korelasi – {station}")
            plt.tight_layout()
            st.pyplot(fig6)
            plt.close()

    st.markdown("**Kecepatan Angin (WSPM) vs PM2.5**")
    if "WSPM" in df.columns:
        fig7, ax7 = plt.subplots(figsize=(10, 4))
        for station in selected_stations:
            sub = df[df["station"] == station].sample(min(3000, len(df)), random_state=42)
            ax7.scatter(sub["WSPM"], sub["PM2.5"], alpha=0.25, s=8,
                        color=PALETTE.get(station), label=station)
        ax7.set_xlabel("Kecepatan Angin WSPM (m/s)")
        ax7.set_ylabel("PM2.5 (µg/m³)")
        ax7.set_title("Hubungan Angin vs PM2.5")
        ax7.legend()
        plt.tight_layout()
        st.pyplot(fig7)
        plt.close()

    with st.expander("📌 Insight"):
        st.markdown(
            """
- Terdapat **korelasi negatif** antara WSPM (kecepatan angin) dan PM2.5 – angin kencang membersihkan polutan.
- Dongsi menunjukkan **resistensi lebih tinggi** sehingga butuh kecepatan angin lebih besar untuk efek yang sama.
- Suhu (TEMP) berkorelasi negatif dengan PM2.5 – udara panas umumnya meningkatkan dispersi polutan.
"""
        )

with tab4:
    st.subheader("Analisis RFM – Karakteristik Polusi")
    st.caption(
        "Recency · Frequency · Intensity – mengidentifikasi risiko aktif polusi di setiap wilayah"
    )

    THRESHOLD = st.slider("Ambang Polusi Tidak Sehat (PM2.5)", 25, 150, 75, step=5)

    high_df = df[df["PM2.5"] > THRESHOLD]

    if high_df.empty:
        st.warning("Tidak ada data yang melewati ambang batas ini.")
    else:
        rfm = (
            high_df.groupby("station")
            .agg(
                Last_High_Pollution=("datetime", "max"),
                Frequency=("datetime", "count"),
                Intensity=("PM2.5", "mean"),
            )
            .reset_index()
        )
        recent_date = df["datetime"].max()
        rfm["Recency_Hours"] = (
            (recent_date - rfm["Last_High_Pollution"]).dt.total_seconds() / 3600
        ).round(1)

        display_rfm = rfm[["station", "Recency_Hours", "Frequency", "Intensity"]].rename(
            columns={
                "station": "Wilayah",
                "Recency_Hours": "Recency (Jam sejak terakhir tidak sehat)",
                "Frequency": "Frequency (Jumlah jam tidak sehat)",
                "Intensity": "Intensity (Rata-rata PM2.5 saat tidak sehat µg/m³)",
            }
        )
        st.dataframe(display_rfm.style.format({"Intensity (Rata-rata PM2.5 saat tidak sehat µg/m³)": "{:.1f}"}), use_container_width=True)

        # Visual bar charts
        fig8, axes = plt.subplots(1, 3, figsize=(14, 4))
        metrics = [
            ("Frequency", "Frequency (Jam Tidak Sehat)", "skyblue"),
            ("Intensity", "Intensity (Avg PM2.5 µg/m³)", "salmon"),
            ("Recency_Hours", "Recency (Jam sejak terakhir)", "gold"),
        ]
        for ax, (col, label, color) in zip(axes, metrics):
            bars = ax.bar(rfm["station"], rfm[col],
                          color=[PALETTE.get(s, color) for s in rfm["station"]])
            ax.set_title(label)
            ax.set_ylabel(label)
            for bar, val in zip(bars, rfm[col]):
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() * 1.01,
                        f"{val:,.0f}",
                        ha="center", va="bottom", fontsize=9)
        plt.tight_layout()
        st.pyplot(fig8)
        plt.close()

    with st.expander("📌 Insight"):
        st.markdown(
            """
- **Dongsi** memiliki *Frequency* jauh lebih tinggi – penduduk pusat kota lebih sering terpapar udara tidak sehat.
- *Intensity* Dongsi juga lebih tinggi – saat polusi terjadi, kadarnya lebih pekat & berbahaya.
- Nilai *Recency* rendah di kedua wilayah menandakan polusi masih menjadi **ancaman aktif**, bukan sekadar kejadian masa lalu.
"""
        )

st.markdown("---")
st.caption(
    "📘 Proyek Analisis Data – Air Quality Dataset | "
    "Henokh William Christianos Lase | henokhwcl | Dicoding Dev Academy"
)
