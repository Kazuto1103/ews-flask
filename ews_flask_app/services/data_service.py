import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from config import Config

# Signal smoothing attempt
try:
    from scipy.signal import savgol_filter
    SAVGOL_AVAILABLE = True
except ImportError:
    SAVGOL_AVAILABLE = False

DATA_DIR = Path(__file__).parent.parent.parent / 'data'

def get_dynamic_date_range():
    """
    Returns start_date fixed at 2021-06-01 and end_date dynamically set to current date.
    """
    start_date = "2021-06-01"
    end_date = datetime.now().strftime('%Y-%m-%d')
    return start_date, end_date

def preprocess_dataframe(df_input):
    """
    Transforms raw precipitation, humidity, and temperature data into model features.
    """
    df_raw = pd.DataFrame({
        'Rain_Raw': df_input['precipitation'],
        'Humidity_Raw': df_input['relative_humidity_2m'],
        'Temperature_Raw': df_input['temperature_2m']
    })
    df_raw.index = pd.to_datetime(df_input['time'])

    df = df_raw.copy()
    # Log1p transformation for rain skewness
    df['Rain'] = np.log1p(df['Rain_Raw'])

    # Savitzky-Golay filtering if available, otherwise simple window smoothing
    if SAVGOL_AVAILABLE and len(df) >= 5:
        try:
            df['Rain'] = savgol_filter(df['Rain'], 5, 2)
        except Exception:
            df['Rain'] = df['Rain'].rolling(window=3, min_periods=1).mean()
    else:
        df['Rain'] = df['Rain'].rolling(window=3, min_periods=1).mean()

    df['Rain_MA'] = df['Rain'].rolling(window=6).mean().fillna(0.0)
    df['Humidity'] = df['Humidity_Raw']
    df['Temperature'] = df['Temperature_Raw']

    df_clean = df.dropna()
    return df_raw, df_clean

def fetch_open_meteo_live(location_name, start_date=None, end_date=None):
    """
    Fetches historical & recent hourly meteorological data directly from Open-Meteo API.
    """
    coords = Config.LOCATIONS.get(location_name)
    if not coords:
        raise ValueError(f"Unknown location name: {location_name}")

    if not start_date or not end_date:
        start_date, end_date = get_dynamic_date_range()

    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={coords['lat']}&longitude={coords['lon']}&"
        f"start_date={start_date}&end_date={end_date}&"
        f"hourly=precipitation,relative_humidity_2m,temperature_2m&"
        f"timezone=Asia%2FJakarta"
    )

    response = requests.get(url, timeout=12)
    response.raise_for_status()
    json_data = response.json()

    if 'hourly' not in json_data:
        raise ValueError(f"Unexpected response structure from Open-Meteo: {json_data}")

    hourly = json_data['hourly']
    df_input = pd.DataFrame({
        'time': hourly['time'],
        'precipitation': hourly['precipitation'],
        'relative_humidity_2m': hourly['relative_humidity_2m'],
        'temperature_2m': hourly['temperature_2m']
    })

    return preprocess_dataframe(df_input)

def load_location_data(location_name, force_live=False):
    """
    Dual-mode data loader:
    1. Checks local CSV file in data/ folder.
    2. If missing or force_live is True, fetches live Open-Meteo data.
    Returns (df_raw, df_clean, data_source_name).
    """
    start_date, end_date = get_dynamic_date_range()
    csv_file = DATA_DIR / f"{location_name}_raw.csv"

    if not force_live and csv_file.exists():
        try:
            df_load = pd.read_csv(csv_file)
            if 'time' in df_load.columns and 'precipitation' in df_load.columns:
                df_raw, df_clean = preprocess_dataframe(df_load)
                return df_raw, df_clean, "Local CSV Repository"
        except Exception as e:
            print(f"[DataService] Warning: Failed to load local CSV {csv_file}: {e}")

    # Fallback / Live Mode via Open-Meteo
    try:
        df_raw, df_clean = fetch_open_meteo_live(location_name, start_date, end_date)
        return df_raw, df_clean, "Open-Meteo API Live"
    except Exception as e:
        print(f"[DataService] Warning: Failed to fetch Open-Meteo live data for {location_name}: {e}")

    # Final fallback to mock generator
    from services import mock_service
    df_mock = mock_service.generate_mock_historical_data(location_name)
    df_raw = pd.DataFrame({
        'Rain_Raw': df_mock['Rain_Raw'],
        'Humidity_Raw': df_mock['Humidity_Raw'],
        'Temperature_Raw': df_mock['Temperature_Raw']
    }, index=df_mock.index)
    return df_raw, df_mock, "Mock Service"
