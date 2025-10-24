from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from app.config import Config
from app.adapters.cache import DataCache

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin():
    """Admin settings page."""
    config = Config()
    settings = {
        'dial_at_a_time': config.DEFAULT_DIAL_AT_A_TIME,
        'max_attempts': config.DEFAULT_MAX_ATTEMPTS,
        'attempts_per_day': config.DEFAULT_ATTEMPTS_PER_DAY,
        'cooldown_days': config.COOLDOWN_DAYS,
        'pilot_list_name': config.PILOT_LIST_NAME,
        'target_connect_uplift_pct': config.TARGET_CONNECT_UPLIFT_PCT,
        'success_connect_uplift_pct': config.SUCCESS_CRITERIA_CONNECT_UPLIFT_PCT,
        'success_voicemail_uplift_pct': config.SUCCESS_CRITERIA_VOICEMAIL_UPLIFT_PCT,
        'timezone': config.TIMEZONE
    }
    
    # Check if data files exist
    data_files = {
        'kixie': os.path.exists(config.DATA_KIXIE),
        'telesign_with': os.path.exists(config.DATA_TELESIGN_WITH),
        'telesign_without': os.path.exists(config.DATA_TELESIGN_WITHOUT),
        'powerlist': os.path.exists(config.DATA_POWERLIST)
    }
    
    return render_template('admin/settings.html', 
                         settings=settings, 
                         data_files=data_files)

@admin_bp.route('/settings', methods=['POST'])
def update_settings():
    """Update configuration settings."""
    # In a production app, you'd want to persist these to a database
    # For now, we'll just flash a message
    flash('Settings updated successfully! (Note: Changes are temporary in this demo)', 'success')
    return redirect(url_for('admin.admin'))

@admin_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('admin.admin'))
    
    file = request.files['file']
    file_type = request.form.get('file_type')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('admin.admin'))
    
    if file and file_type:
        # Create data directory if it doesn't exist
        os.makedirs('./data', exist_ok=True)
        
        # Determine filename based on file type
        filename_map = {
            'kixie': 'kixie_call_history.csv',
            'telesign_with': 'telesign_with_live.csv',
            'telesign_without': 'telesign_without_live.csv',
            'powerlist': 'powerlist_contacts.csv'
        }
        
        filename = filename_map.get(file_type, secure_filename(file.filename))
        filepath = os.path.join('./data', filename)
        
        # Validate CSV format before saving
        try:
            import pandas as pd
            df = pd.read_csv(file)
            
            # Check if file is empty
            if df.empty:
                flash('Uploaded file is empty. Please upload a file with data.', 'error')
                return redirect(url_for('admin.admin'))
            
            # Check required columns based on file type (with flexible matching)
            required_columns = {
                'kixie': ['Disposition', 'To Number'],  # Disposition and To Number are required
                'telesign_with': ['phone_e164'],  # Only phone column is required, others are optional
                'telesign_without': ['phone_e164'],  # Only phone column is required, others are optional
                'powerlist': ['Phone Number', 'Connected', 'Attempt Count']  # List Name is optional
            }
            
            # Define flexible column mappings for common variations
            column_mappings = {
                'kixie': {
                    'Disposition': ['Disposition', 'disposition', 'Outcome', 'outcome', 'Call Outcome', 'call_outcome', 'No Call Outcome'],
                    'To Number': ['To Number', 'to_number', 'To', 'to', 'Phone', 'phone', 'Phone Number', 'phone_number', 'Number', 'number']
                },
                'telesign_with': {
                    'phone_e164': ['phone_e164', 'contact_mobile_phone', 'phone', 'mobile_phone', 'Contact Mobile Phone']
                },
                'telesign_without': {
                    'phone_e164': ['phone_e164', 'contact_mobile_phone', 'phone', 'mobile_phone', 'Contact Mobile Phone']
                },
                'powerlist': {
                    'Phone Number': ['Phone Number', 'phone_number', 'Phone', 'phone', 'PhoneNumber'],
                    'Connected': ['Connected', 'connected', 'Is Connected', 'is_connected'],
                    'Attempt Count': ['Attempt Count', 'attempt_count', 'Attempts', 'attempts', 'Attempts Count'],
                    'List Name': ['List Name', 'list_name', 'List', 'list', 'ListName', 'Powerlist Name', 'powerlist_name']
                }
            }
            
            required = required_columns.get(file_type, [])
            missing_columns = []
            
            if file_type in column_mappings:
                # Use flexible column matching
                mappings = column_mappings[file_type]
                for required_col in required:
                    possible_names = mappings.get(required_col, [required_col])
                    if not any(name in df.columns for name in possible_names):
                        missing_columns.append(required_col)
            else:
                # Use exact matching for other file types
                missing_columns = [col for col in required if col not in df.columns]
            
            if missing_columns:
                flash(f'Invalid CSV format. Missing required columns: {", ".join(missing_columns)}. Available columns: {", ".join(df.columns.tolist())}', 'error')
                return redirect(url_for('admin.admin'))
            
            # Save the file
            file.save(filepath)
            
            # Clear cache to force reload
            cache = DataCache()
            cache.clear_cache()
            
            flash(f'File uploaded successfully: {filename}', 'success')
            
        except Exception as e:
            flash(f'Error processing CSV file: {str(e)}', 'error')
    else:
        flash('Invalid file type', 'error')
    
    return redirect(url_for('admin.admin'))

@admin_bp.route('/refresh')
def refresh_data():
    """Refresh data from files."""
    cache = DataCache()
    cache.clear_cache()
    flash('Data refreshed successfully!', 'success')
    return redirect(url_for('admin.admin'))

@admin_bp.route('/export/summary')
def export_summary():
    """Export summary PDF."""
    # This would generate a PDF summary
    # For now, return a placeholder response
    return jsonify({'message': 'PDF export not implemented in this demo'})

