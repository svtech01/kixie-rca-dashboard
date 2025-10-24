import pandas as pd
from app.services.data_loader import normalize_phones_last10

class ValidationMerger:
    def __init__(self, data):
        self.data = data
        self.kixie_df = data.get('kixie', pd.DataFrame())
        self.powerlist_df = data.get('powerlist', pd.DataFrame())
        self.telesign_df = data.get('telesign', pd.DataFrame())
    
    def cross_reference_data(self):
        """
        Cross-reference Powerlist ↔ Telesign ↔ Kixie data.
        Returns validated_dialed, validated_only, dialed_only, carrier summary, false negatives.
        """
        if self.powerlist_df.empty or self.telesign_df.empty or self.kixie_df.empty:
            return self._empty_results()
        
        # Merge powerlist with telesign
        powerlist_telesign = pd.merge(
            self.powerlist_df,
            self.telesign_df,
            on='phone_normalized',
            how='left',
            suffixes=('_powerlist', '_telesign')
        )
        
        # Merge with kixie calls
        all_data = pd.merge(
            powerlist_telesign,
            self.kixie_df,
            on='phone_normalized',
            how='left',
            suffixes=('', '_kixie')
        )
        
        # Categorize contacts
        validated_dialed = all_data[
            (all_data['is_reachable'].notna()) & 
            (all_data['datetime'].notna())
        ]
        
        validated_only = all_data[
            (all_data['is_reachable'].notna()) & 
            (all_data['datetime'].isna())
        ]
        
        dialed_only = all_data[
            (all_data['is_reachable'].isna()) & 
            (all_data['datetime'].notna())
        ]
        
        # Carrier breakdown
        carrier_summary = self.telesign_df.groupby('carrier').agg({
            'phone_normalized': 'count',
            'is_reachable': lambda x: (x == True).sum()  # Fix: Use True instead of 'Yes'
        }).rename(columns={
            'phone_normalized': 'total_validated',
            'is_reachable': 'reachable_count'
        })
        carrier_summary['reachable_pct'] = (
            carrier_summary['reachable_count'] / carrier_summary['total_validated'] * 100
        ).round(2)
        
        # False negatives (connected even when is_reachable = False)
        false_negatives = all_data[
            (all_data['is_reachable'] == False) & 
            (all_data['Disposition'].isin(['Connected', 'Left voicemail']))
        ]
        
        return {
            'validated_dialed': {
                'count': len(validated_dialed),
                'data': validated_dialed[['Phone Number', 'List Name', 'is_reachable', 'carrier', 'Disposition', 'datetime']].to_dict('records')
            },
            'validated_only': {
                'count': len(validated_only),
                'data': validated_only[['Phone Number', 'List Name', 'is_reachable', 'carrier']].to_dict('records')
            },
            'dialed_only': {
                'count': len(dialed_only),
                'data': dialed_only[['Phone Number', 'List Name', 'Disposition', 'datetime']].to_dict('records')
            },
            'carrier_summary': carrier_summary.to_dict('index'),
            'false_negatives': {
                'count': len(false_negatives),
                'data': false_negatives[['Phone Number', 'List Name', 'is_reachable', 'Disposition', 'datetime']].to_dict('records')
            }
        }
    
    def calculate_data_hygiene_metrics(self):
        """
        Calculate data hygiene metrics.
        """
        if self.telesign_df.empty:
            return {}
        
        total_validated = len(self.telesign_df)
        reachable_count = len(self.telesign_df[self.telesign_df['is_reachable'] == True])  # Fix: Use True instead of 'Yes'
        invalid_count = total_validated - reachable_count
        
        # Count of validated numbers actually dialed
        if not self.kixie_df.empty:
            validated_dialed_count = len(pd.merge(
                self.telesign_df,
                self.kixie_df,
                on='phone_normalized',
                how='inner'
            ))
        else:
            validated_dialed_count = 0
        
        return {
            'total_validated': total_validated,
            'reachable_count': reachable_count,
            'invalid_count': invalid_count,
            'invalid_pct': round(invalid_count / total_validated * 100, 2) if total_validated > 0 else 0,
            'validated_dialed_count': validated_dialed_count,
            'validated_dialed_pct': round(validated_dialed_count / total_validated * 100, 2) if total_validated > 0 else 0
        }
    
    def _empty_results(self):
        """Return empty results when data is missing."""
        return {
            'validated_dialed': {'count': 0, 'data': []},
            'validated_only': {'count': 0, 'data': []},
            'dialed_only': {'count': 0, 'data': []},
            'carrier_summary': {},
            'false_negatives': {'count': 0, 'data': []}
        }

