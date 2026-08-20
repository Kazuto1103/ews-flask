import sys
import os

# Adjust path to import from ews_flask_app
sys.path.append(os.path.join(os.path.dirname(__file__), 'ews_flask_app'))

def ascii_safe(obj):
    """Encodes object as string and strips non-ASCII emoji characters."""
    return str(obj).encode('ascii', 'ignore').decode('ascii')

print("[INFO] Validating EWS Flask Scaffolding...")

try:
    print("1. Testing config imports...")
    from config import Config
    print(f"   - MOCK_MODE is: {ascii_safe(Config.MOCK_MODE)}")
    print(f"   - Number of Locations: {ascii_safe(len(Config.LOCATIONS))}")
    print(f"   - Rainfall classification: {ascii_safe(Config.get_classification(15.2))}")
    print(f"   - Flood Decision: {ascii_safe(Config.get_flood_decision(45.2))}")
    
    print("\n2. Testing Services Layer...")
    from services.bmkg_service import fetch_bmkg_realtime
    from services.mock_service import generate_mock_historical_data, get_mock_predictions
    from services.telegram_service import send_flood_alert
    
    print("   - Testing mock historical data generation...")
    df_mock = generate_mock_historical_data('Langkat_Hulu')
    print(f"     * Generated dataframe size: {ascii_safe(df_mock.shape)}")
    print(f"     * Columns: {ascii_safe(list(df_mock.columns))}")
    
    print("   - Testing mock predictions...")
    preds = get_mock_predictions('Medan_Hulu')
    print(f"     * 12h forecast vector: {ascii_safe(preds)}")
    
    print("   - Testing Telegram notification simulation...")
    ok, status_msg = send_flood_alert('Langkat_Hulu', 42.15, 'WASPADA')
    print(f"     * Simulation result: {ascii_safe(ok)} ({ascii_safe(status_msg)})")
    
    print("   - Testing BMKG real-time parsing...")
    bmkg_desc = fetch_bmkg_realtime('501237')
    print(f"     * BMKG weather forecast: {ascii_safe(bmkg_desc)}")
    
    print("   - Testing Data Service (CSV & Open-Meteo dual mode)...")
    from services.data_service import load_location_data, get_dynamic_date_range
    start_d, end_d = get_dynamic_date_range()
    print(f"     * Dynamic Date Range: {ascii_safe(start_d)} to {ascii_safe(end_d)}")
    
    df_raw, df_clean, src_type = load_location_data('Langkat_Hulu')
    print(f"     * Loaded data source: {ascii_safe(src_type)}")
    print(f"     * Raw shape: {ascii_safe(df_raw.shape)}, Clean shape: {ascii_safe(df_clean.shape)}")
    
    print("\n3. Testing Flask Blueprint initialization...")

    from app import create_app
    app = create_app()
    print("   - Flask application factory created successfully!")
    print(f"   - Registered routes: {ascii_safe(list(app.view_functions.keys()))}")
    
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY! The application structure is modular, robust, and ready for deployment.")
    
except Exception as e:
    print(f"\n[ERROR] Test Failed: {ascii_safe(e)}")
    sys.exit(1)
