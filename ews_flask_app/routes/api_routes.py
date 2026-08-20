from flask import Blueprint, jsonify, request
from config import Config
from services import ml_service
from services import telegram_service
from services.bmkg_service import fetch_bmkg_realtime

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/locations-data')
def locations_data():
    """
    Returns geographical coordinates, 12-hour forecast vectors, and BMKG status
    for all monitoring locations. Consumed by Leaflet.js map in map.js.
    """
    locations_list = []
    for name, coords in Config.LOCATIONS.items():
        preds = ml_service.get_12h_predictions(name)
        bmkg_code = Config.BMKG_MAPPING.get(name, '')
        bmkg_status = fetch_bmkg_realtime(bmkg_code)

        # Per-hour classification for map circle coloring
        classifications = []
        for p in preds:
            kategori, status, warna = Config.get_classification(p)
            classifications.append({
                'value': p,
                'kategori': kategori,
                'status': status,
                'color': warna
            })

        # Pre-compute 3h / 6h accumulation for JS
        accum_3h = round(sum(preds[:3]), 2)
        accum_6h = round(sum(preds[:6]), 2)
        status_3h, color_3h = Config.get_flood_decision(accum_3h)
        status_6h, color_6h = Config.get_flood_decision(accum_6h)

        locations_list.append({
            'id': name,
            'name': name.replace('_', ' '),
            'lat': coords['lat'],
            'lon': coords['lon'],
            'predictions': preds,
            'classifications': classifications,
            'bmkg_status': bmkg_status,
            'accum_3h': accum_3h,
            'status_3h': status_3h,
            'color_3h': color_3h,
            'accum_6h': accum_6h,
            'status_6h': status_6h,
            'color_6h': color_6h,
        })

    return jsonify({'success': True, 'locations': locations_list})


@api_bp.route('/api/trigger-alert', methods=['POST'])
def trigger_alert():
    """
    Sends a single-location Telegram flood alert.
    Body JSON: { "location": "Langkat_Hulu", "accumulation": 45.2,
                 "status": "...", "hours": 6 }
    """
    data = request.get_json() or {}
    location   = data.get('location')
    accumulation = data.get('accumulation')
    status     = data.get('status', '')
    hours      = int(data.get('hours', 6))

    if not location or accumulation is None:
        return jsonify({
            'success': False,
            'message': 'Parameter tidak lengkap. Kirimkan location dan accumulation.'
        }), 400

    # Attach the 12-hour prediction vector for hourly breakdown in the message
    predictions = ml_service.get_12h_predictions(location)

    success, msg = telegram_service.send_flood_alert(
        location=location,
        accumulation=float(accumulation),
        status=status,
        hours=hours,
        predictions=predictions,
    )

    return jsonify({'success': success, 'message': msg})


@api_bp.route('/api/broadcast-all', methods=['POST'])
def broadcast_all():
    """
    Sends the full 4-location status summary report to Telegram.
    Can be triggered manually from the dashboard or called by the scheduler.
    """
    # Gather live predictions and flood decisions for all locations
    all_predictions = {}
    flood_status    = {}

    for name in Config.LOCATIONS.keys():
        preds = ml_service.get_12h_predictions(name)
        all_predictions[name] = preds

        accum_3h = sum(preds[:3])
        accum_6h = sum(preds[:6])
        status_3h, color_3h = Config.get_flood_decision(accum_3h)
        status_6h, color_6h = Config.get_flood_decision(accum_6h)

        flood_status[name] = {
            'accum_3h': round(accum_3h, 2),
            'status_3h': status_3h,
            'color_3h': color_3h,
            'accum_6h': round(accum_6h, 2),
            'status_6h': status_6h,
            'color_6h': color_6h,
        }

    success, msg = telegram_service.send_full_broadcast(all_predictions, flood_status)
    return jsonify({'success': success, 'message': msg})


@api_bp.route('/api/test-telegram', methods=['POST'])
def test_telegram():
    """
    Sends a quick test ping to verify Telegram bot credentials.
    """
    success, msg = telegram_service.test_connection()
    return jsonify({'success': success, 'message': msg})
