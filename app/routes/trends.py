from flask import Blueprint, render_template, jsonify
import pandas as pd
from app.adapters.cache import DataCache
from app.services.metrics import MetricsCalculator

trends_bp = Blueprint('trends', __name__, url_prefix='/trends')

@trends_bp.route('/')
def trends():
    """Trends page with weekly charts."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('kixie'), pd.DataFrame) or data['kixie'].empty:
        return render_template('dashboard/trends.html', 
                             weekly_trends={}, 
                             last_updated=None)
    
    metrics_calc = MetricsCalculator(data)
    weekly_trends = metrics_calc.calculate_weekly_trends()
    
    return render_template('dashboard/trends.html',
                         weekly_trends=weekly_trends,
                         last_updated=data['last_updated'])

@trends_bp.route('/api/weekly')
def api_weekly():
    """API endpoint for weekly trends data."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('kixie'), pd.DataFrame) or data['kixie'].empty:
        return jsonify({})
    
    metrics_calc = MetricsCalculator(data)
    return jsonify(metrics_calc.calculate_weekly_trends())

