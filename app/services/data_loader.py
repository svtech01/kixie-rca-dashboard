import pandas as pd
import os
from datetime import datetime
import pytz
from app.config import Config

def normalize_phones_last10(series):
    """
    Normalize phone numbers to last 10 digits for matching.
    Handles E.164 format (+1234567890) and local formats.
    """
    def normalize_phone(phone):
        if pd.isna(phone):
            return None
        phone_str = str(phone).strip()
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone_str))
        # Return last 10 digits
        return digits[-10:] if len(digits) >= 10 else digits
    
    return series.apply(normalize_phone)

def load_kixie(path):
    """
    Load Kixie call history data.
    Expected columns: Date, Time, Agent First Name, Agent Last Name, 
    Status, Disposition, Duration, Source, To Number
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    
    try:
        # Read CSV with proper headers
        df = pd.read_csv(path)
        
        # Check if file is empty
        if df.empty:
            print(f"Warning: {path} is empty. Returning empty DataFrame.")
            return pd.DataFrame()
        
        # Check if this is the old format (no headers, data starts with date)
        if len(df.columns) == 8 and str(df.columns[0]).startswith('7/'):  # Date-like first column
            df = pd.read_csv(path, header=None)
            df.columns = ['Date', 'Time', 'Agent First Name', 'Agent Last Name', 'Empty', 'Call Type', 'Status', 'Disposition']
        else:
            # This is the new format with proper headers - map to standard names
            column_mapping = {}
            for col in df.columns:
                col_lower = col.lower().replace(' ', '_').replace('-', '_')
                if col_lower in ['to_number', 'to', 'phone', 'phone_number', 'number']:
                    column_mapping[col] = 'To Number'
                elif col_lower in ['disposition', 'outcome', 'call_outcome']:
                    column_mapping[col] = 'Disposition'
                elif col_lower in ['date', 'call_date']:
                    column_mapping[col] = 'Date'
                elif col_lower in ['time', 'call_time']:
                    column_mapping[col] = 'Time'
                elif col_lower in ['agent_first_name', 'first_name', 'agent']:
                    column_mapping[col] = 'Agent First Name'
                elif col_lower in ['agent_last_name', 'last_name']:
                    column_mapping[col] = 'Agent Last Name'
                elif col_lower in ['status', 'call_status']:
                    column_mapping[col] = 'Status'
                elif col_lower in ['duration', 'call_duration']:
                    column_mapping[col] = 'Duration'
                elif col_lower in ['source', 'call_source']:
                    column_mapping[col] = 'Source'
            
            # Rename columns to standard names
            df = df.rename(columns=column_mapping)
        
        # Check if we have the essential columns after mapping
        if 'Disposition' not in df.columns:
            print(f"Warning: {path} does not have required 'Disposition' column. Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error reading {path}: {str(e)}. Returning empty DataFrame.")
        return pd.DataFrame()
    
    # Parse datetime
    if 'Date' in df.columns and 'Time' in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
    elif 'Date' in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'], errors='coerce')
    else:
        df['datetime'] = pd.NaT
    
    # Normalize phone numbers
    if 'To Number' in df.columns:
        df['phone_normalized'] = normalize_phones_last10(df['To Number'])
    
    # Add agent full name
    if 'Agent First Name' in df.columns and 'Agent Last Name' in df.columns:
        df['agent_name'] = df['Agent First Name'].fillna('') + ' ' + df['Agent Last Name'].fillna('')
    else:
        df['agent_name'] = 'Unknown'
    
    return df

def load_telesign(with_path, without_path):
    """
    Load Telesign validation data from both files.
    Expected columns: phone_e164, is_reachable, risk_level, carrier, validation_type
    """
    dfs = []
    
    for path in [with_path, without_path]:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                
                # Check if file is empty
                if df.empty:
                    print(f"Warning: {path} is empty. Skipping.")
                    continue
                
                # Map flexible column names to standard names
                column_mapping = {}
                phone_column = None
                
                for col in df.columns:
                    col_lower = col.lower().replace(' ', '_').replace('-', '_')
                    if col_lower in ['phone_e164', 'contact_mobile_phone', 'phone', 'mobile_phone']:
                        column_mapping[col] = 'phone_e164'
                        phone_column = 'phone_e164'
                    elif col_lower in ['is_reachable', 'reachable', 'live']:
                        column_mapping[col] = 'is_reachable'
                    elif col_lower in ['carrier', 'phone_carrier']:
                        column_mapping[col] = 'carrier'
                    elif col_lower in ['risk_level', 'risk']:
                        column_mapping[col] = 'risk_level'
                    elif col_lower in ['validation_type', 'validation']:
                        column_mapping[col] = 'validation_type'
                
                # Rename columns to standard names
                df = df.rename(columns=column_mapping)
                
                # Check if we have a phone column after mapping
                if phone_column not in df.columns:
                    print(f"Warning: {path} does not have required phone column. Available columns: {df.columns.tolist()}")
                    continue
                
                
                # Add default values for missing columns
                if 'is_reachable' not in df.columns:
                    # For files with "with_live" in name, assume all are reachable
                    if 'with_live' in path.lower():  # Fix: Use more specific check
                        df['is_reachable'] = True
                    else:
                        df['is_reachable'] = False
                
                # Add a source column to track which file the data came from
                df['source_file'] = 'with_live' if 'with_live' in path.lower() else 'without_live'
                
                if 'carrier' not in df.columns:
                    df['carrier'] = 'Unknown'
                
                if 'risk_level' not in df.columns:
                    df['risk_level'] = 'Unknown'
                
                if 'validation_type' not in df.columns:
                    df['validation_type'] = 'Unknown'
                    
                df['phone_normalized'] = normalize_phones_last10(df[phone_column])
                dfs.append(df)
                
            except Exception as e:
                print(f"Error reading {path}: {str(e)}. Skipping.")
                continue
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def load_powerlist(path):
    """
    Load Powerlist contacts data.
    Expected columns: Phone Number, Connected, Attempt Count, List Name
    """
    if not os.path.exists(path):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(path)
        
        # Check if file is empty
        if df.empty:
            print(f"Warning: {path} is empty. Returning empty DataFrame.")
            return pd.DataFrame()
        
        # Map flexible column names to standard names
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().replace(' ', '_').replace('-', '_')
            if col_lower in ['phone_number', 'phone', 'phonenumber']:
                column_mapping[col] = 'Phone Number'
            elif col_lower in ['connected', 'is_connected']:
                column_mapping[col] = 'Connected'
            elif col_lower in ['attempt_count', 'attempts', 'attempts_count']:
                column_mapping[col] = 'Attempt Count'
            elif col_lower in ['list_name', 'list', 'listname', 'powerlist_name']:
                column_mapping[col] = 'List Name'
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Check if required columns exist after mapping
        if 'Phone Number' not in df.columns:
            print(f"Warning: {path} does not have required 'Phone Number' column. Available columns: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Add default List Name if missing
        if 'List Name' not in df.columns:
            df['List Name'] = 'Default List'
            
    except Exception as e:
        print(f"Error reading {path}: {str(e)}. Returning empty DataFrame.")
        return pd.DataFrame()
    
    # Normalize phone numbers
    if 'Phone Number' in df.columns:
        df['phone_normalized'] = normalize_phones_last10(df['Phone Number'])
    
    # Ensure numeric columns
    if 'Connected' in df.columns:
        df['Connected'] = pd.to_numeric(df['Connected'], errors='coerce').fillna(0)
    if 'Attempt Count' in df.columns:
        df['Attempt Count'] = pd.to_numeric(df['Attempt Count'], errors='coerce').fillna(0)
    
    return df

def load_all_data():
    """
    Load all data sources and return as a dictionary.
    """
    config = Config()
    
    data = {
        'kixie': load_kixie(config.DATA_KIXIE),
        'telesign': load_telesign(config.DATA_TELESIGN_WITH, config.DATA_TELESIGN_WITHOUT),
        'powerlist': load_powerlist(config.DATA_POWERLIST),
        'last_updated': datetime.now(pytz.timezone(config.TIMEZONE))
    }
    
    return data

