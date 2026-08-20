import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env relative to this file's directory (works regardless of CWD)
_env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=_env_path)

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_change_me_in_production')
    
    # Toggle Mock Mode (defaults to True)
    MOCK_MODE = os.getenv('MOCK_MODE', 'True').lower() in ('true', '1', 'yes')
    
    # Telegram Credentials
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    
    # Core constants from notebook
    LOCATIONS = {
        'Langkat_Hulu': {'lat': 3.30, 'lon': 98.05},
        'Medan_Hulu': {'lat': 3.15, 'lon': 98.50},
        'Sibolga_Hulu': {'lat': 1.75, 'lon': 98.83},
        'Tapteng_Hulu': {'lat': 2.05, 'lon': 98.65}
    }
    
    BMKG_MAPPING = {
        'Langkat_Hulu': '501237',
        'Medan_Hulu': '501212',
        'Sibolga_Hulu': '501198',
        'Tapteng_Hulu': '501191'
    }
    
    FEATURES = ['Rain', 'Humidity', 'Temperature', 'Rain_MA']
    N_STEPS = 24
    O_STEPS = 12
    
    # Local Data directory
    DATA_DIR = Path(__file__).parent.parent / 'data'
    
    # Data directory if mock mode is False
    GDRIVE_LOAD_DIR = os.getenv('GDRIVE_LOAD_DIR', str(DATA_DIR))
    
    @staticmethod
    def get_current_date_indonesian():
        """Returns today's date formatted in Indonesian style e.g. 5 Agustus 2026."""
        from datetime import datetime
        months = [
            'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        now = datetime.now()
        return f"{now.day} {months[now.month - 1]} {now.year}"

    @staticmethod
    def get_classification(rain_val):
        """Rainfall classification matching the notebook."""
        if rain_val <= 0.5: 
            return "Berawan/Cerah", "✅ AMAN", "#2ecc71"
        elif 0.5 < rain_val <= 20: 
            return "Hujan Ringan", "✅ AMAN", "#3498db"
        elif 20 < rain_val <= 50: 
            return "Hujan Sedang", "⚠️ WASPADA", "#f1c40f"
        elif 50 < rain_val <= 100: 
            return "Hujan Lebat", "🚨 SIAGA", "#e67e22"
        else: 
            return "Hujan Sangat Lebat", "🆘 BAHAYA", "#e74c3c"
            
    @staticmethod
    def get_flood_decision(accum_val):
        """Flood decision matching the notebook."""
        if accum_val < 30:
            return "🟢 AMAN (Tidak Terjadi Banjir)", "#2ecc71"
        elif 30 <= accum_val <= 50:
            return "🟡 WASPADA (Potensi Luapan Sungai/Genangan)", "#f1c40f"
        else:
            return "🔴 BAHAYA (Terjadi Banjir Luapan Sungai)", "#e74c3c"

