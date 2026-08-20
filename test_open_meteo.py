import sys
import os

# Ensure ews_flask_app is on sys.path regardless of execution directory
app_dir = os.path.join(os.path.dirname(__file__), 'ews_flask_app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from services.data_service import fetch_open_meteo_live, get_dynamic_date_range

def main():
    start_d, end_d = get_dynamic_date_range()
    print("=" * 60)
    print(f"[TEST] Live Open-Meteo API Fetching")
    print(f"       Date Range: {start_d} to {end_d}")
    print("=" * 60)

    for loc in ['Langkat_Hulu', 'Medan_Hulu', 'Sibolga_Hulu', 'Tapteng_Hulu']:
        try:
            # Test recent sample range for fast response
            df_raw, df_clean = fetch_open_meteo_live(loc, start_date='2026-08-01', end_date=end_d)
            print(f"[SUCCESS] {loc:15s} -> Raw rows: {len(df_raw)}, Clean rows: {len(df_clean)}")
            print(f"          Latest Timestamp: {df_clean.index[-1]}")
        except Exception as e:
            print(f"[ERROR] {loc:15s} -> {e}")

    print("=" * 60)

if __name__ == '__main__':
    main()
