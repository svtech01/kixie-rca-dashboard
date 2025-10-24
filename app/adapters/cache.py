import json
import os
import pandas as pd
from datetime import datetime, timedelta
from app.services.data_loader import load_all_data

class DataCache:
    def __init__(self, cache_file='./data/cache.json'):
        # Use /tmp for Vercel (read-only filesystem elsewhere)
        default_cache_path = '/tmp/cache.json' if os.environ.get("VERCEL") else './data/cache.json'
        self.cache_file = cache_file or default_cache_path
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    def get_cached_data(self):
        """
        Get cached data if it exists and is not expired.
        """
        if not os.path.exists(self.cache_file):
            return None
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.cache_duration:
                return None
            
            # Convert cached data back to pandas DataFrames
            data = cache_data['data']
            if 'kixie' in data and isinstance(data['kixie'], list):
                data['kixie'] = pd.DataFrame(data['kixie']) if data['kixie'] else pd.DataFrame()
            if 'powerlist' in data and isinstance(data['powerlist'], list):
                data['powerlist'] = pd.DataFrame(data['powerlist']) if data['powerlist'] else pd.DataFrame()
            if 'telesign' in data and isinstance(data['telesign'], list):
                data['telesign'] = pd.DataFrame(data['telesign']) if data['telesign'] else pd.DataFrame()
            
            # Convert last_updated back to datetime
            if 'last_updated' in data and data['last_updated']:
                data['last_updated'] = datetime.fromisoformat(data['last_updated'])
            
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def cache_data(self, data):
        """
        Cache data with timestamp.
        """
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Convert DataFrames to dictionaries for JSON serialization
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': {
                'kixie': data['kixie'].to_dict('records') if not data['kixie'].empty else {},
                'powerlist': data['powerlist'].to_dict('records') if not data['powerlist'].empty else {},
                'telesign': data['telesign'].to_dict('records') if not data['telesign'].empty else {},
                'last_updated': data['last_updated'].isoformat() if data.get('last_updated') else None
            }
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, default=str)
    
    def get_data(self):
        """
        Get data from cache or load fresh data.
        """
        cached_data = self.get_cached_data()
        if cached_data is not None:
            return cached_data
        
        # Load fresh data
        data = load_all_data()
        self.cache_data(data)
        return data
    
    def clear_cache(self):
        """
        Clear the cache.
        """
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)

