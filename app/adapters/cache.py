import json
import os
import pandas as pd
from datetime import datetime, timedelta
from app.services.data_loader import load_all_data

class DataCache:
    def __init__(self, cache_file=None):
        # Use /tmp for Vercel (read-only filesystem elsewhere)
        default_cache_path = '/tmp/cache.json' if os.environ.get("VERCEL") else './data/cache.json'
        self.cache_file = cache_file or default_cache_path
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour

    def get_cached_datax(self):
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
            data['kixie'] = pd.DataFrame(data['kixie']) if data.get('kixie') else pd.DataFrame()
            data['powerlist'] = pd.DataFrame(data['powerlist']) if data.get('powerlist') else pd.DataFrame()
            data['telesign'] = pd.DataFrame(data['telesign']) if data.get('telesign') else pd.DataFrame()

            if data.get('last_updated'):
                data['last_updated'] = datetime.fromisoformat(data['last_updated'])

            return data
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None
        
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
            data['kixie'] = pd.DataFrame(data['kixie']) if data.get('kixie') else pd.DataFrame()
            data['powerlist'] = pd.DataFrame(data['powerlist']) if data.get('powerlist') else pd.DataFrame()
            data['telesign'] = pd.DataFrame(data['telesign']) if data.get('telesign') else pd.DataFrame()

            # Restore datetime types where applicable
            for key in ['kixie', 'telesign', 'powerlist']:
                df = data.get(key)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    for col in df.columns:
                        if 'date' in col.lower() or 'time' in col.lower() or col.lower() == 'datetime':
                            df[col] = pd.to_datetime(df[col], errors='coerce')

            # Restore last updated timestamp
            if data.get('last_updated'):
                data['last_updated'] = datetime.fromisoformat(data['last_updated'])

            return data

        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            return None

    def cache_data(self, data):
        """
        Cache data with timestamp.
        """
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        except OSError:
            # On Vercel, this might fail if not /tmp — safe to ignore
            pass

        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': {
                'kixie': data['kixie'].to_dict('records') if not data['kixie'].empty else {},
                'powerlist': data['powerlist'].to_dict('records') if not data['powerlist'].empty else {},
                'telesign': data['telesign'].to_dict('records') if not data['telesign'].empty else {},
                'last_updated': data.get('last_updated').isoformat() if data.get('last_updated') else None
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

        data = load_all_data()
        self.cache_data(data)
        return data

    def clear_cache(self):
        """
        Clear the cache.
        """
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)