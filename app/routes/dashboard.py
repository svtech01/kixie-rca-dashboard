from flask import Blueprint, render_template, request, jsonify
import pandas as pd
from app.adapters.cache import DataCache
from app.services.metrics import MetricsCalculator
from app.services.validation_merge import ValidationMerger
from app.services.cooldown import CooldownManager

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """Main dashboard page."""
    cache = DataCache()
    data = cache.get_data()
    
    # Check if data is properly loaded and contains DataFrames
    if not data or not isinstance(data.get('kixie'), pd.DataFrame) or data['kixie'].empty:
        return render_template('dashboard/index.html', 
                             baseline_metrics={}, 
                             pilot_metrics={}, 
                             validation_metrics={},
                             cooldown_metrics={},
                             last_updated=None)
    
    # Calculate metrics
    metrics_calc = MetricsCalculator(data)
    validation_merger = ValidationMerger(data)
    cooldown_manager = CooldownManager(data)
    
    baseline_metrics = metrics_calc.calculate_baseline_metrics()
    pilot_metrics = metrics_calc.calculate_pilot_metrics()
    validation_metrics = validation_merger.calculate_data_hygiene_metrics()
    cooldown_metrics = cooldown_manager.calculate_reattempt_potential()
    
    return render_template('dashboard/index.html',
                         baseline_metrics=baseline_metrics,
                         pilot_metrics=pilot_metrics,
                         validation_metrics=validation_metrics,
                         cooldown_metrics=cooldown_metrics,
                         last_updated=data['last_updated'])

@dashboard_bp.route('/api/baseline')
def api_baseline():
    """API endpoint for baseline metrics."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('kixie'), pd.DataFrame) or data['kixie'].empty:
        return jsonify({})
    
    metrics_calc = MetricsCalculator(data)
    return jsonify(metrics_calc.calculate_baseline_metrics())

@dashboard_bp.route('/api/pilot')
def api_pilot():
    """API endpoint for pilot metrics."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('powerlist'), pd.DataFrame) or data['powerlist'].empty:
        return jsonify({})
    
    # Get parameters from request
    dial_at_a_time = request.args.get('dial_at_a_time', type=int)
    max_attempts = request.args.get('max_attempts', type=int)
    
    metrics_calc = MetricsCalculator(data)
    return jsonify(metrics_calc.calculate_pilot_metrics(dial_at_a_time, max_attempts))

