import requests

# Open-Meteo WMO weather code to Indonesian description mapping
WMO_WEATHER_CODES = {
    0:  "☀️ Cerah (Clear Sky)",
    1:  "🌤️ Cerah Berawan (Mainly Clear)",
    2:  "⛅ Berawan Sebagian (Partly Cloudy)",
    3:  "☁️ Berawan Mendung (Overcast)",
    45: "🌫️ Berkabut (Foggy)",
    48: "🌫️ Kabut Beku (Rime Fog)",
    51: "🌦️ Gerimis Ringan (Light Drizzle)",
    53: "🌦️ Gerimis Sedang (Moderate Drizzle)",
    55: "🌧️ Gerimis Lebat (Dense Drizzle)",
    61: "🌧️ Hujan Ringan (Light Rain)",
    63: "🌧️ Hujan Sedang (Moderate Rain)",
    65: "⛈️ Hujan Lebat (Heavy Rain)",
    80: "🌧️ Hujan Lokal (Isolated Shower)",
    81: "⛈️ Hujan Lebat Lokal (Heavy Shower)",
    82: "⛈️ Hujan Sangat Lebat (Violent Shower)",
    95: "⛈️ Hujan Petir (Thunderstorm)",
    96: "⛈️ Hujan Petir + Hujan Es",
    99: "⛈️ Hujan Petir + Hujan Es Lebat",
}

def fetch_bmkg_realtime(area_id):
    """
    DEPRECATED: BMKG XML API now returns 403 Forbidden (Cloudflare-blocked).
    This wrapper calls the Open-Meteo replacement instead to fetch real-time data.
    """
    mappings = {
        '501237': (3.30, 98.05),  # Langkat_Hulu
        '501212': (3.15, 98.50),  # Medan_Hulu
        '501198': (1.75, 98.83),  # Sibolga_Hulu
        '501191': (2.05, 98.65)   # Tapteng_Hulu
    }
    coords = mappings.get(str(area_id))
    if coords:
        lat, lon = coords
        return fetch_openmeteo_current(lat, lon)
    return "Kondisi tidak diketahui"

def fetch_openmeteo_current(lat: float, lon: float, location_name: str = "") -> str:
    """
    Fetches current weather description from Open-Meteo Forecast API.
    Uses WMO weather code to produce a human-readable Indonesian description
    with current precipitation and temperature values.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,precipitation,weather_code&"
        f"timezone=Asia%2FJakarta"
    )
    try:
        res = requests.get(url, timeout=8)
        if res.status_code != 200:
            return f"Open-Meteo Error (Status {res.status_code})"

        data = res.json()
        current = data.get("current", {})
        
        code    = int(current.get("weather_code", 0))
        temp    = current.get("temperature_2m", 0)
        humidity = current.get("relative_humidity_2m", 0)
        precip  = current.get("precipitation", 0.0)
        
        weather_desc = WMO_WEATHER_CODES.get(code, f"Kondisi Cuaca (Kode {code})")
        
        return (
            f"{weather_desc} | "
            f"{precip:.1f} mm | "
            f"{temp:.1f}°C | "
            f"RH {humidity}%"
        )
    except requests.exceptions.Timeout:
        return "⚠️ Open-Meteo Timeout (Periksa koneksi)"
    except Exception as e:
        return f"⚠️ Open-Meteo Error: {str(e)[:60]}"
