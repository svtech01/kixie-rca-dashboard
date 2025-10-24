from flask import Blueprint, render_template, jsonify, request
import pandas as pd
from app.adapters.cache import DataCache
from app.services.metrics import MetricsCalculator
from app.services.cooldown import CooldownManager

powerlist_bp = Blueprint('powerlist', __name__, url_prefix='/powerlist')

@powerlist_bp.route('/')
def powerlist():
    """Powerlist analytics page."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('powerlist'), pd.DataFrame) or data['powerlist'].empty:
        return render_template('dashboard/powerlist.html', 
                             attempt_distribution={}, 
                             cooldown_feed=[],
                             last_updated=None)
    
    # Get list name filter
    list_name = request.args.get('list_name', '')
    
    metrics_calc = MetricsCalculator(data)
    cooldown_manager = CooldownManager(data)
    
    attempt_distribution = metrics_calc.calculate_attempt_distribution(list_name)
    cooldown_feed = cooldown_manager.get_cooldown_feed()
    
    # Get available list names
    available_lists = data['powerlist']['List Name'].unique().tolist() if not data['powerlist'].empty else []
    
    return render_template('dashboard/powerlist.html',
                         attempt_distribution=attempt_distribution,
                         cooldown_feed=cooldown_feed,
                         available_lists=available_lists,
                         selected_list=list_name,
                         last_updated=data['last_updated'])

@powerlist_bp.route('/api/attempts')
def api_attempts():
    """API endpoint for attempt distribution."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('powerlist'), pd.DataFrame) or data['powerlist'].empty:
        return jsonify({})
    
    list_name = request.args.get('list_name', '')
    metrics_calc = MetricsCalculator(data)
    return jsonify(metrics_calc.calculate_attempt_distribution(list_name))

@powerlist_bp.route('/api/cooldown')
def api_cooldown():
    """API endpoint for cooldown feed."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('powerlist'), pd.DataFrame) or data['powerlist'].empty:
        return jsonify([])
    
    cooldown_manager = CooldownManager(data)
    return jsonify(cooldown_manager.get_cooldown_feed())

