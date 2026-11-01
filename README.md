# FIFA Player Analytics · FIFA 23

Dashboard visualisasi data pemain FIFA 23 (musim 2022/23) menggunakan Flask, Pandas, dan Chart.js. Dataset ini bukan data FIFA terbaru. Seluruh tampilan dashboard, CSS, dan JavaScript berada dalam satu file `templates/dashboard.html`.

## Fitur

- Ringkasan jumlah pemain, negara, tim, dan rata-rata rating.
- Analitik market value: rata-rata value, value tertinggi, top 10 pemain berdasarkan value, serta total value tertinggi berdasarkan klub atau negara.
- Filter berdasarkan pencarian, negara, tim, posisi, rating minimum, dan usia maksimum.
- Visualisasi komposisi posisi, negara teratas, distribusi rating, performa tim, dan usia vs rating.
- Tabel pemain terurut berdasarkan `Overall_Rating` dan `Future Potential`, dengan pagination 100 baris per halaman.
- Layout responsive untuk desktop, tablet, dan mobile.
- Data diproses dari `data/Fifa.csv` menggunakan endpoint Flask agar halaman tetap ringan.

## Struktur Folder

```text
data-visualization/
├── app.py
├── data/
│   └── Fifa.csv
├── templates/
│   └── dashboard.html
├── requirements.txt
└── README.md
```

## Menjalankan Dashboard

Pastikan Python 3.10 atau versi lebih baru sudah tersedia, lalu jalankan dari folder `data-visualization`:

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Buka alamat berikut di browser:

```text
http://127.0.0.1:5000
```

### Command Prompt

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Chart.js dan Google Fonts dimuat melalui CDN, sehingga koneksi internet diperlukan ketika membuka halaman dashboard.

## Kolom Dataset

Dashboard menggunakan kolom berikut dari `Fifa.csv`:

- `Name`
- `Country`
- `Position`
- `Age`
- `Overall_Rating`
- `Future Potential`
- `Team`
- `Value Per M$`
- `Total_Stats Score`
