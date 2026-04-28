import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Air Quality Dashboard – Dongsi vs Dingling",
    page_icon="🌫️",
    layout="wide",
)

PALETTE = {
    "Dongsi": "#C0392B",   
    "Dingling": "#2E86C1", 
    
}

STATION_COORDS = {
    "Dongsi": {"lat": 39.929, "lon": 116.417},
    "Dingling": {"lat": 40.285, "lon": 116.220}
}

HEALTHY_LINE_COLOR = "#E67E22"  
HEALTHY_LINE_DASH  = "dash"

def hex_to_rgba(hex_val, opacity=0.1):
    hex_val = hex_val.lstrip('#')
    rgb = tuple(int(hex_val[i:i+2], 16) for i in range(0, 6, 2))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap');
    html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
    .kpi-card {{ 
        background: #ffffff; /* Tetap putih agar kontras dengan border warna stasiun */
        border-radius: 10px; 
        padding: 14px 18px; 
        border-left: 5px solid #ccc; 
        box-shadow: 0 1px 4px rgba(0,0,0,.1); 
        margin-bottom: 8px; 
    }}

    /* Perbaikan: Gunakan warna hitam pekat agar tetap terbaca meski di dark mode */
    .kpi-label {{ 
        font-size: .75rem; 
        color: #1a1a1a !important; /* Warna gelap agar terlihat di bg putih */
        margin-bottom: 2px; 
        font-weight: 600;
    }}

    .kpi-value {{ 
        font-size: 1.5rem; 
        font-weight: 700; 
        color: #000000 !important; /* Warna hitam solid */
        font-family: 'IBM Plex Mono', monospace; 
    }}

    .kpi-sub {{ 
        font-size: .75rem; 
        color: #4b5563 !important; /* Abu-abu gelap */
    }}
    
    /* ... sisa CSS lainnya ... */
    </style>
    """,
    unsafe_allow_html=True,
)

def render_legend_banner(stations):
    dots = "".join(
        f'<span><span class="legend-dot" style="background:{PALETTE.get(s, "#888")}"></span>'
        f'<strong>{s}</strong></span>'
        for s in stations
    )
    st.markdown(
        f'<div class="legend-banner">🗺️ <strong>Legenda Warna:</strong> {dots} &nbsp;&nbsp; '
        f'<span><span class="legend-line"></span>Batas Sehat WHO (75 µg/m³)</span></div>',
        unsafe_allow_html=True,
    )

@st.cache_data
def load_data(filepath: str) -> pd.DataFrame:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(filepath):
        filepath = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(filepath):
        return pd.DataFrame()

    df = pd.read_csv(filepath)
    if "No" in df.columns: df.drop("No", axis=1, inplace=True)
    
    num_cols = df.select_dtypes(include=["float64", "int64"]).columns
    df[num_cols] = df[num_cols].interpolate(method="linear")
    if "wd" in df.columns: df["wd"] = df["wd"].ffill()
    
    df["datetime"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
    def season(m):
        if m in [12, 1, 2]: return "Winter"
        if m in [3, 4, 5]:  return "Spring"
        if m in [6, 7, 8]:  return "Summer"
        return "Autumn"
    df["season"] = df["month"].apply(season)
    return df

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Flag_of_the_People%27s_Republic_of_China.svg/320px-Flag_of_the_People%27s_Republic_of_China.svg.png", width=80)
    st.title("⚙️ Pengaturan")
    data_dir = "main_data.csv" 
    df_raw = load_data(data_dir)

    if df_raw.empty:
        st.error("❌ File tidak ditemukan. Periksa path CSV Anda.")
        st.stop()

    stations = sorted(df_raw["station"].unique().tolist())
    sel_stations = st.multiselect("Pilih Stasiun", stations, default=stations)
    year_range = st.slider("Rentang Tahun", int(df_raw["year"].min()), int(df_raw["year"].max()), (int(df_raw["year"].min()), int(df_raw["year"].max())))
    st.markdown("---")
    st.caption("Proyek Analisis Data – Air Quality Dataset\n\n**Henokh William Christianos Lase**")

df = df_raw[df_raw["station"].isin(sel_stations) & df_raw["year"].between(year_range[0], year_range[1])].copy()
if df.empty:
    st.warning("Tidak ada data untuk filter tersebut.")
    st.stop()

st.title("🌫️ Dashboard Kualitas Udara – Beijing")
st.markdown("Perbandingan **PM2.5** antara wilayah urban **Dongsi** dan pinggiran **Dingling** (2013–2017)")
render_legend_banner(sel_stations)
st.markdown("---")

kpi_cols = st.columns(len(sel_stations) * 2)
for i, station in enumerate(sel_stations):
    subset = df[df["station"] == station]["PM2.5"]
    css_cls = "dongsi" if station == "Dongsi" else "dingling"
    bad_pct = (subset > 75).mean() * 100
    
    with kpi_cols[i*2]:
        st.markdown(f'<div class="kpi-card {css_cls}"><div class="kpi-label">📍 {station} – Avg PM2.5</div>'
                    f'<div class="kpi-value">{subset.mean():.1f} <small>µg/m³</small></div>'
                    f'<div class="kpi-sub">Maks {subset.max():.0f} | Min {subset.min():.0f}</div></div>', unsafe_allow_html=True)
    with kpi_cols[i*2+1]:
        st.markdown(f'<div class="kpi-card {css_cls}"><div class="kpi-label">⚠️ % Jam Tidak Sehat</div>'
                    f'<div class="kpi-value">{bad_pct:.1f}<small>%</small></div>'
                    f'<div class="kpi-sub">{len(subset):,} jam pengamatan</div></div>', unsafe_allow_html=True)

st.markdown("---")
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tren Bulanan", "🌸 Pola Musiman", "🔬 EDA & Korelasi", "🌍 Analisis Geospasial"])

with tab1:
    st.subheader("Tren Rata-rata PM2.5 Bulanan")
    trend_df = df.groupby(["year", "month", "station"])["PM2.5"].mean().reset_index()
    trend_df["period"] = pd.to_datetime(trend_df["year"].astype(str) + "-" + trend_df["month"].astype(str).str.zfill(2))
    trend_df.sort_values("period", inplace=True)

    fig1 = go.Figure()
    for station in sel_stations:
        sub = trend_df[trend_df["station"] == station]
        color = PALETTE.get(station, "#888")
        fig1.add_trace(go.Scatter(
            x=sub["period"], y=sub["PM2.5"],
            name=station, mode="lines",
            line=dict(color=color, width=2.5),
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.15), 
            hovertemplate=f"<b>{station}</b><br>Periode: %{{x|%b %Y}}<br>PM2.5: <b>%{{y:.1f}} µg/m³</b><extra></extra>"
        ))

    fig1.add_hline(y=75, line_color=HEALTHY_LINE_COLOR, line_dash=HEALTHY_LINE_DASH, 
                   annotation_text="Batas Sehat (75 µg/m³)", annotation_position="top left")
    fig1.update_layout(xaxis_title="Tahun-Bulan", yaxis_title="µg/m³", hovermode="x unified", height=420, template="plotly_white")
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.subheader("Tingkat Polusi PM2.5 Berdasarkan Musim")
    season_order = ["Spring", "Summer", "Autumn", "Winter"]
    seasonal = df.groupby(["season", "station"])["PM2.5"].mean().reset_index()
    seasonal["season"] = pd.Categorical(seasonal["season"], categories=season_order, ordered=True)
    seasonal.sort_values("season", inplace=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig2 = px.bar(seasonal, x="season", y="PM2.5", color="station", color_discrete_map=PALETTE, barmode="group", title="Rata-rata PM2.5 per Musim")
        fig2.add_hline(y=75, line_color=HEALTHY_LINE_COLOR, line_dash=HEALTHY_LINE_DASH)
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        fig3 = px.line(seasonal, x="season", y="PM2.5", color="station", color_discrete_map=PALETTE, markers=True, title="Tren Musiman PM2.5")
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Eksplorasi Data & Korelasi Meteorologi")
    col_c, col_d = st.columns(2)
    with col_c:
        fig4 = go.Figure()
        for s in sel_stations:
            fig4.add_trace(go.Histogram(x=df[df["station"] == s]["PM2.5"], name=s, opacity=0.6, marker_color=PALETTE.get(s)))
        fig4.update_layout(barmode="overlay", title="Distribusi PM2.5")
        st.plotly_chart(fig4, use_container_width=True)
    with col_d:
        fig5 = go.Figure()
        for s in sel_stations:
            fig5.add_trace(go.Box(y=df[df["station"] == s]["PM2.5"], name=s, marker_color=PALETTE.get(s)))
        fig5.update_layout(title="Box Plot Sebaran PM2.5")
        st.plotly_chart(fig5, use_container_width=True)

with tab4:
    st.subheader("Peta Sebaran Konsentrasi PM2.5")
    st.markdown("Visualisasi posisi geografis stasiun terhadap intensitas polusi rata-rata.")

    # Menyiapkan data geospasial
    geo_df = df.groupby('station')['PM2.5'].mean().reset_index()
    geo_df['lat'] = geo_df['station'].map(lambda x: STATION_COORDS.get(x, {}).get('lat'))
    geo_df['lon'] = geo_df['station'].map(lambda x: STATION_COORDS.get(x, {}).get('lon'))

    fig_map = px.scatter_mapbox(
        geo_df,
        lat="lat",
        lon="lon",
        color="station",
        size="PM2.5",
        color_discrete_map=PALETTE,
        size_max=40,
        zoom=9,
        hover_name="station",
        hover_data={"lat": False, "lon": False, "PM2.5": ":.2f"},
        title="Distribusi Spasial PM2.5 di Beijing"
    )

    fig_map.update_layout(
        mapbox_style="carto-positron", 
        margin={"r":0,"t":40,"l":0,"b":0},
        height=600,
        autosize=True  
    )

    st.plotly_chart(
        fig_map, 
        use_container_width=True,
        theme="streamlit"  
    )

st.markdown("---")
st.caption("📘 Proyek Analisis Data | Henokh William Christianos Lase | Dicoding Dev Academy")
