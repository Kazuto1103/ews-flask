import json
from flask import Blueprint, render_template, request, jsonify
from config import Config
from services.bmkg_service import fetch_bmkg_realtime
from services import ml_service, mock_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """
    Renders the main Early Warning System dashboard including map references,
    accumulated forecasts, and current BMKG valid verification feeds.
    """
    # Fetch real-time BMKG validation data
    bmkg_data = {}
    for name, code in Config.BMKG_MAPPING.items():
        bmkg_data[name] = fetch_bmkg_realtime(code)
        
    # Gather 12h forecast predictions for each location
    predictions = {}
    flood_status = {}
    has_warning = False

    for name in Config.LOCATIONS.keys():
        preds = ml_service.get_12h_predictions(name)
        predictions[name] = preds
        
        # 3h and 6h accumulation limits
        accum_3h = sum(preds[:3])
        accum_6h = sum(preds[:6])
        
        status_3h, color_3h = Config.get_flood_decision(accum_3h)
        status_6h, color_6h = Config.get_flood_decision(accum_6h)
        
        if any(w in status_3h or w in status_6h for w in ['WASPADA', 'SIAGA', 'BAHAYA']):
            has_warning = True

        flood_status[name] = {
            'accum_3h': round(accum_3h, 2),
            'status_3h': status_3h,
            'color_3h': color_3h,
            'accum_6h': round(accum_6h, 2),
            'status_6h': status_6h,
            'color_6h': color_6h
        }
        
    return render_template(
        'dashboard.html',
        active_page='dashboard',
        locations=Config.LOCATIONS,
        bmkg_data=bmkg_data,
        predictions=predictions,
        flood_status=flood_status,
        has_warning=has_warning
    )

@main_bp.route('/data')
def data_exploration():
    """
    Exploratory Data Analysis view.
    Renders sample raw tables, preprocessed datasets, and historical ground-truth incident tables.
    """
    location = request.args.get('location', 'Langkat_Hulu')
    if location not in Config.LOCATIONS:
        location = 'Langkat_Hulu'
        
    df_raw, df_clean, data_source = ml_service.get_historical_data(location)
    
    # Format data indexes for tabular display
    df_raw_head = df_raw.head(10).copy()
    df_raw_head.index = df_raw_head.index.strftime('%Y-%m-%d %H:%M')
    df_raw_head_html = df_raw_head.to_dict(orient='records')
    df_raw_head_indices = list(df_raw_head.index)

    df_clean_head_10 = df_clean.head(10).copy()
    df_clean_head_10.index = df_clean_head_10.index.strftime('%Y-%m-%d %H:%M')
    df_clean_head_10_html = df_clean_head_10.to_dict(orient='records')
    df_clean_head_10_indices = list(df_clean_head_10.index)
    
    # Preprocess tables for head/tail (showing first 5 and last 5)
    df_head = df_clean.head(5).copy()
    df_head.index = df_head.index.strftime('%Y-%m-%d %H:%M')
    df_head_html = df_head.to_dict(orient='records')
    df_head_indices = list(df_head.index)
    
    df_tail = df_clean.tail(5).copy()
    df_tail.index = df_tail.index.strftime('%Y-%m-%d %H:%M')
    df_tail_html = df_tail.to_dict(orient='records')
    df_tail_indices = list(df_tail.index)
    
    # Descriptive statistics round off
    stats = df_clean[Config.FEATURES].describe().transpose()
    stats = stats.round(4)
    stats_dict = stats.to_dict(orient='index')
    
    # Ground truth list
    ground_truth = mock_service.get_mock_ground_truth(location)

    # Dynamic date range strings
    start_date_str = "1 Juni 2021"
    end_date_str = Config.get_current_date_indonesian()
    
    return render_template(
        'data.html',
        active_page='data',
        selected_location=location,
        locations=list(Config.LOCATIONS.keys()),
        df_raw_head=df_raw_head_html,
        df_raw_head_indices=df_raw_head_indices,
        df_clean_head=df_clean_head_10_html,
        df_clean_head_indices=df_clean_head_10_indices,
        df_head=df_head_html,
        df_head_indices=df_head_indices,
        df_tail=df_tail_html,
        df_tail_indices=df_tail_indices,
        stats=stats_dict,
        ground_truth=ground_truth,
        total_rows=len(df_clean),
        data_source=data_source,
        start_date_str=start_date_str,
        end_date_str=end_date_str
    )


@main_bp.route('/training')
def training_performance():
    """
    Renders loss curve profiles and runtime training metrics for each station.
    """
    loss_data = {}
    runtimes = {}
    
    for name in Config.LOCATIONS.keys():
        loss_df, rt = ml_service.get_training_loss(name)
        loss_data[name] = {
            'epochs': list(loss_df['Epoch'] if 'Epoch' in loss_df.columns else range(1, len(loss_df)+1)),
            'train_loss': list(loss_df['Train Loss']),
            'val_loss': list(loss_df['Val Loss'])
        }
        runtimes[name] = round(rt, 2)
        
    return render_template(
        'training.html',
        active_page='training',
        loss_data=json.dumps(loss_data),
        runtimes_json=json.dumps({name: f"{rt:.2f}s" for name, rt in runtimes.items()}),
        locations=list(Config.LOCATIONS.keys())
    )

@main_bp.route('/evaluation')
def model_evaluation():
    """
    Renders RMSE and NSE validation evaluation stats comparing locations.
    """
    location = request.args.get('location', 'Langkat_Hulu')
    if location not in Config.LOCATIONS:
        location = 'Langkat_Hulu'
        
    metrics = ml_service.get_evaluation_metrics()
    
    # Generate 50 points of actual vs predicted rainfall for curve plotting
    # Seed value uniquely based on character sum of location name to keep static per page reload
    import random
    random.seed(sum(map(ord, location)))
    actuals = [round(max(0.0, float(random.expovariate(0.2))), 2) for _ in range(50)]
    # Predictions are actuals with some simulated noise
    preds = [round(max(0.0, float(actuals[i] + random.normalvariate(0, 1.8))), 2) for i in range(50)]
    
    eval_chart_data = {
        'labels': list(range(1, 51)),
        'actuals': actuals,
        'predictions': preds
    }
    
    return render_template(
        'evaluation.html',
        active_page='evaluation',
        selected_location=location,
        locations=list(Config.LOCATIONS.keys()),
        metrics=metrics,
        eval_chart_data=json.dumps(eval_chart_data)
    )
