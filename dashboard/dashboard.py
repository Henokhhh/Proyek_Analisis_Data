import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# Set page configuration
st.set_page_config(page_title="Beijing Air Quality Dashboard", layout="wide")

# --- PENANGANAN PATH FILE ---
# Memastikan file main_data.csv ditemukan meskipun dijalankan dari folder induk
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "main_data.csv")

# --- HELPER FUNCTIONS ---
def create_monthly_trend_df(df):
    monthly_trend = df.groupby(['station', 'month'])['PM2.5'].mean().reset_index()
    return monthly_trend

def create_station_comparison_df(df):
    comparison_df = df.groupby('station')[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean().reset_index()
    return comparison_df

# --- LOAD CLEANED DATA ---
if os.path.exists(csv_path):
    main_df = pd.read_csv(csv_path)
    main_df['datetime'] = pd.to_datetime(main_df[['year', 'month', 'day', 'hour']])
else:
    st.error(f"File {csv_path} tidak ditemukan!")
    st.stop()

# --- SIDEBAR FILTER ---
with st.sidebar:
    st.title("Filter Data")
    min_date = main_df["datetime"].min()
    max_date = main_df["datetime"].max()
    
    # Input rentang waktu
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter data berdasarkan tanggal
filtered_df = main_df[(main_df["datetime"] >= pd.to_datetime(start_date)) & 
                      (main_df["datetime"] <= pd.to_datetime(end_date))]

# --- HEADER UTAMA ---
st.title('📊 Dashboard Kualitas Udara: Dongsi vs Dingling')
st.markdown(f"Analisis kualitas udara periode: **{start_date}** hingga **{end_date}**")

# --- KONTEN UTAMA: METRICS ---
avg_pm25_dongsi = filtered_df[filtered_df['station'] == 'Dongsi']['PM2.5'].mean()
avg_pm25_dingling = filtered_df[filtered_df['station'] == 'Dingling']['PM2.5'].mean()

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Rata-rata PM2.5 Dongsi (Urban)", value=f"{avg_pm25_dongsi:.2f} µg/m³")
with col_m2:
    st.metric(label="Rata-rata PM2.5 Dingling (Pinggiran)", value=f"{avg_pm25_dingling:.2f} µg/m³")

st.divider()

# --- VISUALISASI 1: TREN BULANAN ---
st.subheader("📈 Tren Bulanan PM2.5")
monthly_trend_df = create_monthly_trend_df(filtered_df)

fig, ax = plt.subplots(figsize=(12, 5))
sns.lineplot(
    data=monthly_trend_df, 
    x='month', 
    y='PM2.5', 
    hue='station', 
    marker='o', 
    palette={'Dongsi': '#C0392B', 'Dingling': '#2E86C1'},
    ax=ax
)
ax.set_xticks(range(1, 13))
ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
ax.set_xlabel("Bulan")
st.pyplot(fig)

# --- VISUALISASI 2: PERBANDINGAN POLUTAN ---
st.subheader("📑 Perbandingan Rata-rata Polutan")
comparison_df = create_station_comparison_df(filtered_df)

col1, col2 = st.columns(2)
with col1:
    st.write("**Statistik Dongsi (Urban)**")
    st.dataframe(comparison_df[comparison_df['station'] == 'Dongsi'], use_container_width=True)

with col2:
    st.write("**Statistik Dingling (Pinggiran)**")
    st.dataframe(comparison_df[comparison_df['station'] == 'Dingling'], use_container_width=True)

# --- VISUALISASI 3: KORELASI ANGIN ---
st.subheader("🌬️ Pengaruh Kecepatan Angin (WSPM) terhadap PM2.5")
fig, ax = plt.subplots(1, 2, figsize=(16, 6))

# Mengambil sampel data agar performa dashboard ringan
sample_size = min(500, len(filtered_df[filtered_df['station']=='Dongsi']))

sns.regplot(x='WSPM', y='PM2.5', data=filtered_df[filtered_df['station']=='Dongsi'].sample(sample_size), 
            scatter_kws={'alpha':0.3}, line_kws={'color':'red'}, ax=ax[0])
ax[0].set_title('Dongsi (Pusat Kota)')

sns.regplot(x='WSPM', y='PM2.5', data=filtered_df[filtered_df['station']=='Dingling'].sample(sample_size), 
            scatter_kws={'alpha':0.3}, line_kws={'color':'red'}, ax=ax[1])
ax[1].set_title('Dingling (Pinggiran Kota)')

st.pyplot(fig)

st.caption('Copyright (c) 2026 - Henokh William Christianos Lase | Proyek Analisis Data Dicoding')