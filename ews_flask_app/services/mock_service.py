import pandas as pd
import numpy as np
import datetime

# Seed for reproducibility but slightly dynamic
np.random.seed(42)

# Ground Truth Flood events from the notebook
MOCK_GROUND_TRUTH = {
    'Langkat_Hulu': [
        {"Tanggal Banjir": "02-03 November 2022", "Dampak Hidrologi & Keterangan Lapangan": "Sei Wampu meluap hebat; memutus jalan nasional Trans-Sumatera di Tanjung Pura.", "Referensi": "Antara News", "Akumulasi Hujan H-1 (6-Jam)": "58.45 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "26-28 Desember 2023", "Dampak Hidrologi & Keterangan Lapangan": "Banjir luapan akhir tahun akibat cuaca ekstrem kawasan hulu TNGL.", "Referensi": "Detikcom", "Akumulasi Hujan H-1 (6-Jam)": "44.12 mm", "Kondisi Kejenuhan Hulu": "⚠️ WASPADA (Saturasi Sedang)"},
        {"Tanggal Banjir": "16-18 November 2024", "Dampak Hidrologi & Keterangan Lapangan": "Curah hujan tinggi merata; banjir bandang luapan sungai merusak fasilitas umum.", "Referensi": "CNN Indonesia", "Akumulasi Hujan H-1 (6-Jam)": "62.30 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "26-29 November 2025", "Dampak Hidrologi & Keterangan Lapangan": "Banjir Siklon Koto; luapan total Sei Wampu merendam 16 kecamatan.", "Referensi": "RRI / Antara News", "Akumulasi Hujan H-1 (6-Jam)": "114.80 mm", "Kondisi Kejenuhan Hulu": "🆘 BAHAYA (Saturasi Ekstrem)"}
    ],
    'Medan_Hulu': [
        {"Tanggal Banjir": "18-19 Agustus 2022", "Dampak Hidrologi & Keterangan Lapangan": "Luapan Sungai Deli dan Babura; merendam ribuan unit rumah warga Medan.", "Referensi": "Kompas / Detikcom", "Akumulasi Hujan H-1 (6-Jam)": "52.10 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "19 November 2022", "Dampak Hidrologi & Keterangan Lapangan": "Hujan lebat durasi panjang; banjir menggenangi wilayah Medan Maimun dan Johor.", "Referensi": "Antara News", "Akumulasi Hujan H-1 (6-Jam)": "49.65 mm", "Kondisi Kejenuhan Hulu": "⚠️ WASPADA (Saturasi Sedang)"},
        {"Tanggal Banjir": "27-28 November 2024", "Dampak Hidrologi & Keterangan Lapangan": "Debit banjir kiriman raksasa dari hulu Karo merendam hilir Medan hingga 2 meter.", "Referensi": "CNN Indonesia", "Akumulasi Hujan H-1 (6-Jam)": "78.20 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "27-30 November 2025", "Dampak Hidrologi & Keterangan Lapangan": "Banjir Siklon Tropis Koto ekstrem; Sungai Deli meluap total, 85.000 warga mengungsi.", "Referensi": "Kompas / TVOne", "Akumulasi Hujan H-1 (6-Jam)": "132.50 mm", "Kondisi Kejenuhan Hulu": "🆘 BAHAYA (Saturasi Ekstrem)"}
    ],
    'Sibolga_Hulu': [
        {"Tanggal Banjir": "23-24 Maret 2022", "Dampak Hidrologi & Keterangan Lapangan": "Hujan lebat mendadak memicu luapan bukit hulu Tapian Nauli dan longsor perkotaan.", "Referensi": "Detikcom", "Akumulasi Hujan H-1 (6-Jam)": "68.90 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "12-13 November 2024", "Dampak Hidrologi & Keterangan Lapangan": "Banjir luapan tinggi melanda perbatasan geografis Sibolga-Tapanuli Tengah.", "Referensi": "Antara News", "Akumulasi Hujan H-1 (6-Jam)": "54.15 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "26-28 November 2025", "Dampak Hidrologi & Keterangan Lapangan": "Dampak ekstrem Siklon Koto di pesisir barat; banjir bandang serentak dan longsor.", "Referensi": "Kompas", "Akumulasi Hujan H-1 (6-Jam)": "122.40 mm", "Kondisi Kejenuhan Hulu": "🆘 BAHAYA (Saturasi Ekstrem)"}
    ],
    'Tapteng_Hulu': [
        {"Tanggal Banjir": "18 November 2021", "Dampak Hidrologi & Keterangan Lapangan": "Hujan lebat berdurasi panjang dari hulu perbukitan merendam beberapa kecamatan.", "Referensi": "Antara News", "Akumulasi Hujan H-1 (6-Jam)": "41.50 mm", "Kondisi Kejenuhan Hulu": "⚠️ WASPADA (Saturasi Sedang)"},
        {"Tanggal Banjir": "16-17 Oktober 2023", "Dampak Hidrologi & Keterangan Lapangan": "Pasokan air masif hulu Tapanuli Utara menyebabkan Sungai Batang Toru meluap di Barus.", "Referensi": "Detikcom", "Akumulasi Hujan H-1 (6-Jam)": "50.80 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "26-27 November 2024", "Dampak Hidrologi & Keterangan Lapangan": "Intensitas hujan ekstrem pantai barat memicu banjir luapan dan longsor tanah.", "Referensi": "CNN Indonesia", "Akumulasi Hujan H-1 (6-Jam)": "71.60 mm", "Kondisi Kejenuhan Hulu": "🚨 SIAGA (Saturasi Tinggi)"},
        {"Tanggal Banjir": "26-29 November 2025", "Dampak Hidrologi & Keterangan Lapangan": "Cuaca ekstrem regional bibit siklon 95B memicu luapan masif Sungai Batang Toru.", "Referensi": "Antara News", "Akumulasi Hujan H-1 (6-Jam)": "108.20 mm", "Kondisi Kejenuhan Hulu": "🆘 BAHAYA (Saturasi Ekstrem)"}
    ]
}

def generate_mock_historical_data(name):
    """
    Generates a mock dataframe spanning from 2021-06-01 to 2026-06-01.
    Includes columns: Rain_Raw, Humidity_Raw, Temperature_Raw, Rain, Humidity, Temperature, Rain_MA
    """
    # Generating 5 years of hourly data is large, so let's generate a smaller high-quality sequence 
    # of say 1000 hours, but label the timestamps to start from 2021-06-01 and end at 2026-06-01
    # by using date spacing, or just generate a full 5-year dataset in a simplified form.
    # To keep it lightweight and fast but realistic, we can generate a 10,000-hour sequence.
    hours = 8760 * 2  # ~2 years of hourly data is plenty and fast
    times = pd.date_range(start="2021-06-01", periods=hours, freq="h")
    
    # Generate rain data with many zeros
    rain_raw = np.random.choice([0.0, 0.0, 0.0, 0.0, 0.0, 1.2, 5.5, 12.0, 25.4, 45.0, 60.5, 110.0], 
                                 size=hours, 
                                 p=[0.70, 0.10, 0.08, 0.05, 0.03, 0.02, 0.01, 0.005, 0.003, 0.001, 0.0005, 0.0005])
    
    # Smooth a bit and add small random noise
    rain_raw = np.clip(rain_raw + np.random.uniform(-0.1, 0.1, size=hours), 0, None)
    rain_raw[rain_raw < 0.1] = 0.0
    
    humidity_raw = np.random.uniform(60.0, 98.0, size=hours)
    temperature_raw = np.random.uniform(22.0, 33.0, size=hours)
    
    # Process features as in the notebook
    rain_log = np.log1p(rain_raw)
    
    # Pre-calculated MA
    df = pd.DataFrame({
        'Rain_Raw': rain_raw,
        'Humidity_Raw': humidity_raw,
        'Temperature_Raw': temperature_raw,
        'Rain': rain_log,
        'Humidity': humidity_raw,
        'Temperature': temperature_raw
    }, index=times)
    
    df['Rain_MA'] = df['Rain'].rolling(window=6).mean().fillna(0.0)
    
    return df

def get_mock_training_loss():
    """
    Returns simulated Conv1D-LSTM training loss over 5 epochs.
    """
    return pd.DataFrame({
        'Epoch': [1, 2, 3, 4, 5],
        'Train Loss': [0.0452, 0.0315, 0.0210, 0.0142, 0.0095],
        'Val Loss': [0.0489, 0.0338, 0.0235, 0.0160, 0.0112]
    })

def get_mock_runtime(name):
    """Returns fake training runtime in seconds."""
    runtimes = {
        'Langkat_Hulu': 4.35,
        'Medan_Hulu': 4.82,
        'Sibolga_Hulu': 4.12,
        'Tapteng_Hulu': 4.56
    }
    return runtimes.get(name, 4.0)

def get_mock_metrics():
    """
    Returns RMSE and NSE metrics.
    """
    return {
        'Langkat_Hulu': {'RMSE': 4.1205, 'NSE': 0.7812},
        'Medan_Hulu': {'RMSE': 3.8540, 'NSE': 0.8123},
        'Sibolga_Hulu': {'RMSE': 5.2104, 'NSE': 0.7410},
        'Tapteng_Hulu': {'RMSE': 4.9015, 'NSE': 0.7654}
    }

def get_mock_predictions(name):
    """
    Generates 12-hour ahead precipitation forecasts.
    To make it dynamic and show alerts properly, we can seed with current hour.
    """
    current_hour = datetime.datetime.now().hour
    # Different locations get different weather patterns
    if name == 'Langkat_Hulu':
        # Moderate rain transitioning to heavy
        base_pattern = [0.0, 0.5, 2.0, 8.5, 18.0, 25.0, 22.0, 15.0, 5.0, 1.2, 0.0, 0.0]
    elif name == 'Medan_Hulu':
        # Severe rainfall (Bahaya trigger)
        base_pattern = [1.0, 5.0, 15.0, 35.0, 45.0, 55.0, 30.0, 12.0, 4.0, 0.5, 0.0, 0.0]
    elif name == 'Sibolga_Hulu':
        # Moderate warning
        base_pattern = [0.0, 0.0, 1.0, 3.5, 10.0, 15.0, 12.0, 8.0, 3.0, 0.5, 0.0, 0.0]
    else:
        # Tapteng_Hulu - Clear/Dry transitions
        base_pattern = [0.0, 0.0, 0.0, 0.2, 0.4, 0.5, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0]
        
    # Introduce some variations based on current hour to simulate real-time forecasts
    variation = np.sin(current_hour / 24.0 * np.pi) * 2.0
    predictions = [max(0.0, round(val + (variation if val > 0 else 0), 2)) for val in base_pattern]
    
    return predictions

def get_mock_ground_truth(name):
    """Returns historical flood incidents."""
    return MOCK_GROUND_TRUTH.get(name, [])
