from flask import Blueprint, render_template, jsonify
import pandas as pd
from app.adapters.cache import DataCache
from app.services.validation_merge import ValidationMerger

validation_bp = Blueprint('validation', __name__, url_prefix='/validation')

@validation_bp.route('/')
def validation():
    """Validation cross-reference page."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('telesign'), pd.DataFrame) or data['telesign'].empty:
        return render_template('dashboard/validation.html', 
                             cross_ref_data={}, 
                             hygiene_metrics={},
                             last_updated=None)
    
    validation_merger = ValidationMerger(data)
    cross_ref_data = validation_merger.cross_reference_data()
    hygiene_metrics = validation_merger.calculate_data_hygiene_metrics()
    
    return render_template('dashboard/validation.html',
                         cross_ref_data=cross_ref_data,
                         hygiene_metrics=hygiene_metrics,
                         last_updated=data['last_updated'])

@validation_bp.route('/api/crossref')
def api_crossref():
    """API endpoint for cross-reference data."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('telesign'), pd.DataFrame) or data['telesign'].empty:
        return jsonify({})
    
    validation_merger = ValidationMerger(data)
    return jsonify(validation_merger.cross_reference_data())

@validation_bp.route('/api/hygiene')
def api_hygiene():
    """API endpoint for data hygiene metrics."""
    cache = DataCache()
    data = cache.get_data()
    
    if not data or not isinstance(data.get('telesign'), pd.DataFrame) or data['telesign'].empty:
        return jsonify({})
    
    validation_merger = ValidationMerger(data)
    return jsonify(validation_merger.calculate_data_hygiene_metrics())

