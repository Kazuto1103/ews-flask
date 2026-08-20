import os
from flask import Flask
from config import Config
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from services import ml_service


def create_app():
    """
    Flask Application Factory.
    Initializes configurations, blueprints, loads ML profiles,
    and sends Telegram startup notification.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Run ML training initialization on startup if in real mode
    with app.app_context():
        if not Config.MOCK_MODE:
            print("--- RUNNING IN REAL DATA MODE ---")
            # Try to train LSTM models if TensorFlow is available
            from services import ml_service
            if ml_service.REAL_MODE_AVAILABLE:
                print("TensorFlow detected. Loading CSV data and training deep learning models...")
                success = ml_service.load_and_train_real_models()
                if success:
                    print("Models trained successfully. System is fully live.")
                else:
                    print("Training failed. Predictions will use mock fallback; historical data will use CSV/Open-Meteo.")
            else:
                print("TensorFlow not installed. Predictions use mock; historical data (EDA) will load from CSV / Open-Meteo API.")
        else:
            print("--- RUNNING IN MOCK MODE (SYNTHETIC EWS DATA) ---")

        # Send Telegram startup ping (non-blocking — failure doesn't crash server)
        try:
            from services.telegram_service import send_startup_notification
            ok, msg = send_startup_notification()
            if ok:
                print(f"[Telegram] Startup notification sent successfully.")
            else:
                print(f"[Telegram] Startup notification skipped: {msg}")
        except Exception as e:
            print(f"[Telegram] Startup notification error (non-fatal): {e}")

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
