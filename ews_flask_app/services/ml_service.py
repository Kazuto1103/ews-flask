import os
import pandas as pd
import numpy as np
from config import Config
from services import mock_service, data_service

# Attempt loading dependencies for real mode, but catch errors to fall back to mock
REAL_MODE_AVAILABLE = False
try:
    from scipy.signal import savgol_filter
    from sklearn.preprocessing import MinMaxScaler
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Conv1D, MaxPooling1D, Dropout, BatchNormalization, Input
    from tensorflow.keras.optimizers import Adam
    REAL_MODE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Real ML mode libraries are missing: {e}. Falling back to Mock Mode.")

# In-memory store for models and data when running real mode
_real_db = {}

def is_real_mode_active():
    """Checks if we should run the real model."""
    return (not Config.MOCK_MODE) and REAL_MODE_AVAILABLE

def load_and_train_real_models():
    """
    If running in real mode, loads data via data_service (CSV / Open-Meteo) and trains Conv1D-LSTM models.
    """
    if not is_real_mode_active():
        return False
        
    print("Initiating training pipeline for all 4 stations...")
    for name in Config.LOCATIONS.keys():
        try:
            df_raw, df_clean, data_source = data_service.load_location_data(name)
            
            # Train model
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(df_clean[Config.FEATURES])
            
            X, y = [], []
            for i in range(len(scaled_data) - Config.N_STEPS - Config.O_STEPS + 1):
                X.append(scaled_data[i:(i + Config.N_STEPS), :])
                y.append(scaled_data[(i + Config.N_STEPS):(i + Config.N_STEPS + Config.O_STEPS), 0])
            X, y = np.array(X), np.array(y)

            split = int(0.8 * len(X))
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            model = Sequential([
                Input(shape=(Config.N_STEPS, len(Config.FEATURES))),
                Conv1D(32, 3, activation='relu', padding='same'),
                BatchNormalization(),
                MaxPooling1D(2),
                LSTM(64, return_sequences=False),
                Dropout(0.2),
                Dense(Config.O_STEPS)
            ])
            model.compile(optimizer=Adam(0.001), loss='mse')

            import time
            start_time = time.time()
            history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=5, batch_size=256, verbose=0)
            runtime = time.time() - start_time

            loss_history = pd.DataFrame({
                'Train Loss': history.history['loss'],
                'Val Loss': history.history['val_loss']
            })

            # Save in memory
            _real_db[name] = {
                'raw': df_raw,
                'clean': df_clean,
                'model': model,
                'scaler': scaler,
                'loss_history': loss_history,
                'x_test': X_test,
                'y_test': y_test,
                'runtime': runtime,
                'source': data_source
            }
            print(f"Successfully trained model for {name} ({data_source}) in {runtime:.2f} seconds.")
            
        except Exception as e:
            print(f"Failed to load or train model for {name}: {e}")
            
    return len(_real_db) > 0

# Interface Functions for Routes

def get_historical_data(name):
    """
    Returns (raw_dataframe, clean_dataframe, data_source_string) for a location.
    """
    if is_real_mode_active() and name in _real_db:
        return _real_db[name]['raw'], _real_db[name]['clean'], _real_db[name]['source']
    
    # If not in trained real mode, check if we can load CSV or Open-Meteo via data_service
    if not Config.MOCK_MODE:
        df_raw, df_clean, data_source = data_service.load_location_data(name)
        return df_raw, df_clean, data_source

    # Fallback to mock
    df = mock_service.generate_mock_historical_data(name)
    df_raw = pd.DataFrame({
        'Rain_Raw': df['Rain_Raw'],
        'Humidity_Raw': df['Humidity_Raw'],
        'Temperature_Raw': df['Temperature_Raw']
    }, index=df.index)
    return df_raw, df, "Mock Service"


def get_training_loss(name):
    """
    Returns training loss DataFrame and runtime.
    """
    if is_real_mode_active() and name in _real_db:
        return _real_db[name]['loss_history'], _real_db[name]['runtime']
    return mock_service.get_mock_training_loss(), mock_service.get_mock_runtime(name)

def get_evaluation_metrics(name=None):
    """
    Returns RMSE and NSE dictionary.
    """
    if is_real_mode_active() and name in _real_db:
        # Calculate actual metrics
        model = _real_db[name]['model']
        scaler = _real_db[name]['scaler']
        X_test = _real_db[name]['x_test']
        y_test = _real_db[name]['y_test']
        
        preds_scaled = model.predict(X_test, verbose=0)
        
        def inverse_to_mm(scaled_vector):
            res = []
            for val in scaled_vector:
                dummy = np.zeros((1, len(Config.FEATURES)))
                dummy[0, 0] = val
                res.append(np.clip(np.expm1(scaler.inverse_transform(dummy)[0, 0]), 0, None))
            return np.array(res)
            
        y_true_mm = inverse_to_mm(y_test[:, 0])
        y_pred_mm = inverse_to_mm(preds_scaled[:, 0])
        
        rmse = np.sqrt(np.mean((y_true_mm - y_pred_mm) ** 2))
        
        # Calculate NSE
        num = np.sum((y_true_mm - y_pred_mm)**2)
        den = np.sum((y_true_mm - np.mean(y_true_mm))**2)
        nse = 1 - (num / den) if den != 0 else 0
        
        return {'RMSE': round(float(rmse), 5), 'NSE': round(float(nse), 4)}
        
    if name:
        return mock_service.get_mock_metrics().get(name, {'RMSE': 0.0, 'NSE': 0.0})
    return mock_service.get_mock_metrics()

def get_12h_predictions(name):
    """
    Returns 12-hour predictions.
    """
    if is_real_mode_active() and name in _real_db:
        try:
            model = _real_db[name]['model']
            scaler = _real_db[name]['scaler']
            df_clean = _real_db[name]['clean']
            
            last_window = scaler.transform(df_clean[Config.FEATURES].tail(Config.N_STEPS))
            p_vector = model.predict(last_window.reshape(1, Config.N_STEPS, len(Config.FEATURES)), verbose=0)[0]
            
            actual_preds = []
            for val_scaled in p_vector:
                dummy = np.zeros((1, len(Config.FEATURES)))
                dummy[0, 0] = val_scaled
                val_mm = np.clip(np.expm1(scaler.inverse_transform(dummy)[0, 0]), 0, None)
                actual_preds.append(round(float(val_mm), 2))
            return actual_preds
        except Exception as e:
            print(f"Error evaluating real prediction for {name}: {e}")
            
    return mock_service.get_mock_predictions(name)
