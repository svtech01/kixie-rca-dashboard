import unittest
import pandas as pd
from app.services.validation_merge import ValidationMerger

class TestValidationMerger(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        # Sample Kixie data
        self.kixie_data = pd.DataFrame({
            'datetime': pd.date_range('2024-01-01', periods=10, freq='H'),
            'phone_normalized': ['1234567890', '0987654321', '5555555555', '1111111111', '2222222222'] * 2,
            'Disposition': ['Connected', 'Left voicemail', 'No Answer', 'Busy', 'Connected'] * 2,
            'agent_name': ['Agent 1'] * 10
        })
        
        # Sample Powerlist data
        self.powerlist_data = pd.DataFrame({
            'Phone Number': ['1234567890', '0987654321', '5555555555', '1111111111', '2222222222'],
            'phone_normalized': ['1234567890', '0987654321', '5555555555', '1111111111', '2222222222'],
            'Connected': [1, 1, 0, 1, 0],
            'Attempt Count': [5, 3, 15, 2, 8],
            'List Name': ['NAICS', 'NAICS', 'Other', 'NAICS', 'Other']
        })
        
        # Sample Telesign data
        self.telesign_data = pd.DataFrame({
            'phone_e164': ['+1234567890', '+0987654321', '+5555555555', '+1111111111', '+3333333333'],
            'phone_normalized': ['1234567890', '0987654321', '5555555555', '1111111111', '3333333333'],
            'is_reachable': ['Yes', 'Yes', 'No', 'Yes', 'Yes'],
            'carrier': ['Verizon', 'AT&T', 'Unknown', 'T-Mobile', 'Sprint'],
            'risk_level': ['Low', 'Low', 'High', 'Low', 'Medium']
        })
        
        self.data = {
            'kixie': self.kixie_data,
            'powerlist': self.powerlist_data,
            'telesign': self.telesign_data
        }
    
    def test_cross_reference_data(self):
        """Test cross-reference data calculation."""
        merger = ValidationMerger(self.data)
        cross_ref = merger.cross_reference_data()
        
        # Check that we have all required keys
        required_keys = ['validated_dialed', 'validated_only', 'dialed_only', 'carrier_summary', 'false_negatives']
        for key in required_keys:
            self.assertIn(key, cross_ref)
        
        # Check validated_dialed
        self.assertIn('count', cross_ref['validated_dialed'])
        self.assertIn('data', cross_ref['validated_dialed'])
        
        # Should have some validated and dialed contacts
        self.assertGreater(cross_ref['validated_dialed']['count'], 0)
        
        # Check carrier summary
        self.assertIsInstance(cross_ref['carrier_summary'], dict)
    
    def test_calculate_data_hygiene_metrics(self):
        """Test data hygiene metrics calculation."""
        merger = ValidationMerger(self.data)
        hygiene = merger.calculate_data_hygiene_metrics()
        
        # Check required keys
        required_keys = ['total_validated', 'reachable_count', 'invalid_count', 'invalid_pct', 'validated_dialed_count', 'validated_dialed_pct']
        for key in required_keys:
            self.assertIn(key, hygiene)
        
        # Check that totals make sense
        self.assertEqual(hygiene['total_validated'], 5)  # 5 telesign records
        self.assertEqual(hygiene['reachable_count'], 4)  # 4 reachable
        self.assertEqual(hygiene['invalid_count'], 1)   # 1 invalid
        
        # Check percentages
        expected_invalid_pct = (1 / 5) * 100
        self.assertEqual(hygiene['invalid_pct'], expected_invalid_pct)
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        from app.services.data_loader import normalize_phones_last10
        
        # Test various phone formats
        test_phones = pd.Series([
            '+1234567890',
            '1234567890',
            '+1-234-567-890',
            '123-456-7890',
            '1234567890123',  # More than 10 digits
            '123456789'       # Less than 10 digits
        ])
        
        normalized = normalize_phones_last10(test_phones)
        
        # All should normalize to last 10 digits
        expected = ['1234567890', '1234567890', '1234567890', '1234567890', '4567890123', '123456789']
        
        for i, phone in enumerate(normalized):
            self.assertEqual(phone, expected[i])
    
    def test_empty_data_handling(self):
        """Test handling of empty data."""
        empty_data = {
            'kixie': pd.DataFrame(),
            'powerlist': pd.DataFrame(),
            'telesign': pd.DataFrame()
        }
        
        merger = ValidationMerger(empty_data)
        cross_ref = merger.cross_reference_data()
        hygiene = merger.calculate_data_hygiene_metrics()
        
        # Should return empty results without errors
        self.assertEqual(cross_ref['validated_dialed']['count'], 0)
        self.assertEqual(hygiene.get('total_validated', 0), 0)

if __name__ == '__main__':
    unittest.main()

