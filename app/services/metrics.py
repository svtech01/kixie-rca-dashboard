import pandas as pd
from datetime import datetime, timedelta
import pytz
from app.config import Config

class MetricsCalculator:
    def __init__(self, data):
        self.data = data
        self.config = Config()
        self.kixie_df = data.get('kixie', pd.DataFrame())
        self.powerlist_df = data.get('powerlist', pd.DataFrame())
        self.telesign_df = data.get('telesign', pd.DataFrame())
    
    def calculate_baseline_metrics(self):
        """
        Calculate baseline metrics before any changes.
        """
        if self.kixie_df.empty:
            return {}
        
        # Connect Rate = connected_calls / total_calls
        total_calls = len(self.kixie_df)
        connected_calls = len(self.kixie_df[
            self.kixie_df['Disposition'].isin(self.config.CONNECT_DISPOSITIONS)
        ])
        connect_rate = (connected_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Answer Event % approximation
        # When dial_at_a_time=4, assume only 1/4 reaches answer event
        dial_at_a_time = self.config.DEFAULT_DIAL_AT_A_TIME
        calls_logged_in_history = total_calls
        lost_race_attempts = calls_logged_in_history * (dial_at_a_time - 1) / dial_at_a_time
        answer_event_pct = (calls_logged_in_history / (calls_logged_in_history + lost_race_attempts) * 100) if (calls_logged_in_history + lost_race_attempts) > 0 else 0
        
        # Avg Attempts per Lost-Race Number
        lost_race_df = self.kixie_df[
            ~self.kixie_df['Disposition'].isin(self.config.CONNECT_DISPOSITIONS)
        ]
        if 'phone_normalized' in lost_race_df.columns and not lost_race_df.empty:
            avg_attempts_lost_race = lost_race_df.groupby('phone_normalized').size().mean()
        else:
            avg_attempts_lost_race = 0
        
        # Hitting Cooldown / Day
        max_attempts = self.config.DEFAULT_MAX_ATTEMPTS
        if 'Attempt Count' in self.powerlist_df.columns:
            cooldown_contacts = self.powerlist_df[
                self.powerlist_df['Attempt Count'] >= max_attempts
            ]
            cooldown_per_day = len(cooldown_contacts) / 7 if len(cooldown_contacts) > 0 else 0  # Assuming 7-day period
        else:
            cooldown_per_day = 0
        
        return {
            'connect_rate': round(connect_rate, 2),
            'answer_event_pct': round(answer_event_pct, 2),
            'avg_attempts_lost_race': round(avg_attempts_lost_race, 2),
            'cooldown_per_day': round(cooldown_per_day, 2),
            'total_calls': total_calls,
            'connected_calls': connected_calls
        }
    
    def calculate_pilot_metrics(self, dial_at_a_time_override=None, max_attempts_override=None):
        """
        Calculate pilot metrics for NAICS Powerlist with potential overrides.
        """
        if self.powerlist_df.empty:
            return {}
        
        # Filter for pilot list - if no NAICS contacts, use a sample of all contacts
        pilot_df = self.powerlist_df[
            self.powerlist_df['List Name'].str.contains(self.config.PILOT_LIST_NAME, case=False, na=False)
        ]
        
        # If no NAICS contacts found, use a sample of all contacts for pilot
        if pilot_df.empty:
            # Take a sample of contacts for pilot testing
            sample_size = min(100, len(self.powerlist_df))  # Sample up to 100 contacts
            pilot_df = self.powerlist_df.sample(n=sample_size, random_state=42)
        
        if pilot_df.empty:
            return {}
        
        sample_size = len(pilot_df)
        
        # Use overrides or defaults
        dial_at_a_time = dial_at_a_time_override or self.config.DEFAULT_DIAL_AT_A_TIME
        max_attempts = max_attempts_override or self.config.DEFAULT_MAX_ATTEMPTS
        
        # Calculate expected metrics with overrides
        # This is a simplified calculation - in reality, you'd need historical data
        baseline_metrics = self.calculate_baseline_metrics()
        baseline_connect_rate = baseline_metrics.get('connect_rate', 0)
        
        # Target uplift
        target_connect_rate = baseline_connect_rate * (1 + self.config.TARGET_CONNECT_UPLIFT_PCT / 100)
        
        # Success criteria
        success_connect_uplift = self.config.SUCCESS_CRITERIA_CONNECT_UPLIFT_PCT
        success_voicemail_uplift = self.config.SUCCESS_CRITERIA_VOICEMAIL_UPLIFT_PCT
        
        return {
            'sample_size': sample_size,
            'target_connect_uplift_pct': self.config.TARGET_CONNECT_UPLIFT_PCT,
            'target_connect_rate': round(target_connect_rate, 2),
            'success_connect_uplift_pct': success_connect_uplift,
            'success_voicemail_uplift_pct': success_voicemail_uplift,
            'test_duration_days': 3,
            'dial_at_a_time': dial_at_a_time,
            'max_attempts': max_attempts
        }
    
    def calculate_weekly_trends(self):
        """
        Calculate weekly aggregated trends.
        """
        if self.kixie_df.empty:
            return {}
        
        # Ensure datetime column exists
        if 'datetime' not in self.kixie_df.columns:
            return {}
        
        # Group by week
        df = self.kixie_df.copy()
        df['week'] = df['datetime'].dt.to_period('W')
        
        weekly_stats = df.groupby('week').agg({
            'phone_normalized': 'count',  # Total calls
            'Disposition': lambda x: len(x[x.isin(self.config.CONNECT_DISPOSITIONS)])  # Connected calls
        }).rename(columns={'phone_normalized': 'total_calls', 'Disposition': 'connected_calls'})
        
        # Calculate voicemail and no answer
        weekly_stats['voicemail_calls'] = df[df['Disposition'] == 'Left voicemail'].groupby('week').size()
        weekly_stats['no_answer_calls'] = df[~df['Disposition'].isin(self.config.CONNECT_DISPOSITIONS)].groupby('week').size()
        
        # Fill NaN values
        weekly_stats = weekly_stats.fillna(0)
        
        # Convert to list format for Chart.js
        weeks = [str(week) for week in weekly_stats.index]
        
        return {
            'weeks': weeks,
            'total_calls': weekly_stats['total_calls'].tolist(),
            'connected_calls': weekly_stats['connected_calls'].tolist(),
            'voicemail_calls': weekly_stats['voicemail_calls'].tolist(),
            'no_answer_calls': weekly_stats['no_answer_calls'].tolist()
        }
    
    def calculate_attempt_distribution(self, list_name=None):
        """
        Calculate attempt distribution for a specific powerlist.
        """
        df = self.powerlist_df.copy()
        
        if df.empty or 'Attempt Count' not in df.columns:
            return {}
        
        if list_name:
            df = df[df['List Name'].str.contains(list_name, case=False, na=False)]
        
        if df.empty:
            return {}
        
        # Group by attempt count
        attempt_dist = df['Attempt Count'].value_counts().sort_index()
        
        return {
            'attempt_counts': attempt_dist.index.tolist(),
            'contact_counts': attempt_dist.values.tolist()
        }
    
    def calculate_cooldown_metrics(self):
        """
        Calculate cooldown-related metrics.
        """
        if self.powerlist_df.empty or 'Attempt Count' not in self.powerlist_df.columns:
            return {}
        
        max_attempts = self.config.DEFAULT_MAX_ATTEMPTS
        cooldown_contacts = self.powerlist_df[
            self.powerlist_df['Attempt Count'] >= max_attempts
        ]
        
        # Calculate reattempt potential (simplified)
        cooldown_days = self.config.COOLDOWN_DAYS
        reattempt_date = datetime.now() + timedelta(days=cooldown_days)
        
        return {
            'cooldown_contacts': len(cooldown_contacts),
            'cooldown_days': cooldown_days,
            'reattempt_date': reattempt_date.strftime('%Y-%m-%d'),
            'max_attempts': max_attempts
        }

