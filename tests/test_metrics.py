import unittest
import pandas as pd
from datetime import datetime, timedelta
from app.services.metrics import MetricsCalculator

class TestMetricsCalculator(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        # Sample Kixie data
        self.kixie_data = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=100, freq='H'),
            'phone_normalized': ['1234567890'] * 50 + ['0987654321'] * 50,
            'Disposition': ['Connected'] * 30 + ['Left voicemail'] * 20 + ['No Answer'] * 30 + ['Busy'] * 20,
            'agent_name': ['Agent 1'] * 50 + ['Agent 2'] * 50
        })
        
        # Sample Powerlist data
        self.powerlist_data = pd.DataFrame({
            'Phone Number': ['1234567890', '0987654321', '5555555555'],
            'phone_normalized': ['1234567890', '0987654321', '5555555555'],
            'Connected': [1, 1, 0],
            'Attempt Count': [5, 3, 15],
            'List Name': ['NAICS', 'NAICS', 'Other']
        })
        
        # Sample Telesign data
        self.telesign_data = pd.DataFrame({
            'phone_e164': ['+1234567890', '+0987654321', '+5555555555'],
            'phone_normalized': ['1234567890', '0987654321', '5555555555'],
            'is_reachable': ['Yes', 'Yes', 'No'],
            'carrier': ['Verizon', 'AT&T', 'Unknown'],
            'risk_level': ['Low', 'Low', 'High']
        })
        
        self.data = {
            'kixie': self.kixie_data,
            'powerlist': self.powerlist_data,
            'telesign': self.telesign_data
        }
    
    def test_calculate_baseline_metrics(self):
        """Test baseline metrics calculation."""
        calc = MetricsCalculator(self.data)
        metrics = calc.calculate_baseline_metrics()
        
        # Test connect rate calculation
        expected_connected = 50  # 30 Connected + 20 Left voicemail
        expected_total = 100
        expected_connect_rate = (expected_connected / expected_total) * 100
        
        self.assertEqual(metrics['connect_rate'], expected_connect_rate)
        self.assertEqual(metrics['total_calls'], expected_total)
        self.assertEqual(metrics['connected_calls'], expected_connected)
    
    def test_calculate_pilot_metrics(self):
        """Test pilot metrics calculation."""
        calc = MetricsCalculator(self.data)
        metrics = calc.calculate_pilot_metrics()
        
        # Test sample size (NAICS contacts)
        expected_sample_size = 2  # Two NAICS contacts
        self.assertEqual(metrics['sample_size'], expected_sample_size)
        
        # Test target connect rate calculation
        baseline_metrics = calc.calculate_baseline_metrics()
        expected_target = baseline_metrics['connect_rate'] * 1.3  # 30% uplift
        self.assertEqual(metrics['target_connect_rate'], expected_target)
    
    def test_calculate_weekly_trends(self):
        """Test weekly trends calculation."""
        calc = MetricsCalculator(self.data)
        trends = calc.calculate_weekly_trends()
        
        # Should have weeks data
        self.assertIn('weeks', trends)
        self.assertIn('total_calls', trends)
        self.assertIn('connected_calls', trends)
        
        # Check that we have data for the weeks
        self.assertGreater(len(trends['weeks']), 0)
        self.assertGreater(len(trends['total_calls']), 0)
    
    def test_calculate_attempt_distribution(self):
        """Test attempt distribution calculation."""
        calc = MetricsCalculator(self.data)
        distribution = calc.calculate_attempt_distribution('NAICS')
        
        # Should have attempt counts and contact counts
        self.assertIn('attempt_counts', distribution)
        self.assertIn('contact_counts', distribution)
        
        # Check that we have data
        self.assertGreater(len(distribution['attempt_counts']), 0)
        self.assertGreater(len(distribution['contact_counts']), 0)
    
    def test_calculate_cooldown_metrics(self):
        """Test cooldown metrics calculation."""
        calc = MetricsCalculator(self.data)
        cooldown = calc.calculate_cooldown_metrics()
        
        # Should have cooldown contacts count
        self.assertIn('cooldown_contacts', cooldown)
        self.assertIn('cooldown_days', cooldown)
        
        # One contact should be in cooldown (attempt count >= 10)
        self.assertEqual(cooldown['cooldown_contacts'], 1)

if __name__ == '__main__':
    unittest.main()

