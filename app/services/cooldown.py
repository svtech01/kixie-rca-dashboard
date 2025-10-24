import pandas as pd
from datetime import datetime, timedelta
from app.config import Config

class CooldownManager:
    def __init__(self, data):
        self.data = data
        self.powerlist_df = data.get('powerlist', pd.DataFrame())
        self.kixie_df = data.get('kixie', pd.DataFrame())
        self.config = Config()
    
    def identify_cooldown_contacts(self):
        """
        Identify contacts that have reached max attempts threshold.
        """
        if self.powerlist_df.empty or 'Attempt Count' not in self.powerlist_df.columns:
            return pd.DataFrame()
        
        max_attempts = self.config.DEFAULT_MAX_ATTEMPTS
        cooldown_contacts = self.powerlist_df[
            self.powerlist_df['Attempt Count'] >= max_attempts
        ].copy()
        
        if cooldown_contacts.empty:
            return cooldown_contacts
        
        # Add cooldown information
        cooldown_contacts['cooldown_start'] = datetime.now()
        cooldown_contacts['cooldown_end'] = datetime.now() + timedelta(days=self.config.COOLDOWN_DAYS)
        cooldown_contacts['owner'] = 'System'  # Default owner
        cooldown_contacts['review_date'] = cooldown_contacts['cooldown_end']
        
        return cooldown_contacts
    
    def calculate_reattempt_potential(self):
        """
        Calculate potential for reattempt after cooldown period.
        """
        cooldown_contacts = self.identify_cooldown_contacts()
        
        if cooldown_contacts.empty:
            return {
                'cooldown_contacts_count': 0,
                'reattempt_potential': 0,
                'target_kpi': 15,  # 15% of cooldown contacts should reach voicemail or connect
                'cooldown_days': self.config.COOLDOWN_DAYS
            }
        
        # Calculate potential based on historical data
        # This is a simplified calculation - in reality, you'd analyze historical reattempt success
        total_cooldown = len(cooldown_contacts)
        target_success_rate = 0.15  # 15% target
        reattempt_potential = int(total_cooldown * target_success_rate)
        
        return {
            'cooldown_contacts_count': total_cooldown,
            'reattempt_potential': reattempt_potential,
            'target_kpi': 15,
            'cooldown_days': self.config.COOLDOWN_DAYS,
            'cooldown_contacts': cooldown_contacts[['Phone Number', 'List Name', 'Attempt Count', 'cooldown_end', 'owner']].to_dict('records')
        }
    
    def get_cooldown_feed(self):
        """
        Get a feed of cooldown contacts with their status.
        """
        cooldown_contacts = self.identify_cooldown_contacts()
        
        if cooldown_contacts.empty:
            return []
        
        feed = []
        for _, contact in cooldown_contacts.iterrows():
            feed.append({
                'phone_number': contact['Phone Number'],
                'list_name': contact['List Name'],
                'attempt_count': contact['Attempt Count'],
                'cooldown_start': contact['cooldown_start'].strftime('%Y-%m-%d'),
                'cooldown_end': contact['cooldown_end'].strftime('%Y-%m-%d'),
                'owner': contact['owner'],
                'review_date': contact['review_date'].strftime('%Y-%m-%d'),
                'status': 'In Cooldown'
            })
        
        return feed

