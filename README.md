# Proyek_Analisis_Data Dasboard
## Struktur Direktori
```
├── dashboard/
│   ├── dashboard.py       # File utama aplikasi Streamlit
│   └── main_data.csv      # Dataset hasil pembersihan (Cleaned)
├── data/
│   ├── Dongsi.csv         # Raw dataset wilayah Dongsi
│   └── Dingling.csv       # Raw dataset wilayah Dingling
├── notebook.ipynb         # Proses analisis data (EDA & Cleaning)
├── requirements.txt       # Daftar library yang diperlukan
└── README.md              # Dokumentasi proyek
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run streamlit app
```
streamlit run dashboard/dashboard.py
```

## Fitur Utama Dashboard
* **Filter Rentang Waktu:** Pengguna dapat menentukan periode analisis data secara fleksibel melalui sidebar.
* **Metrik Ringkasan:** Menampilkan angka rata-rata konsentrasi PM2.5 untuk wilayah Dongsi dan Dingling secara dinamis.
* **Tren Bulanan:** Membandingkan pola polusi udara antara pusat kota (Dongsi) dan pinggiran kota (Dingling) sepanjang tahun.
* **Analisis Meteorologi:** Visualisasi korelasi antara kecepatan angin (WSPM) dengan tingkat polusi udara untuk melihat efek pembersihan alami.