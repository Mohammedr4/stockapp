import unittest
from decimal import Decimal
from calculators.reprice_engine import calculate_reprice_by_shares, calculate_reprice_by_target

class TestRepriceEngine(unittest.TestCase):
    def test_reprice_by_shares_valid(self):
        position = {
            'current_shares': '10.00',
            'average_price': '100.00',
            'market_price': '80.00'
        }
        res = calculate_reprice_by_shares(position, Decimal('10.00'))
        self.assertEqual(res['new_average_price'], '90.00')
        self.assertEqual(res['total_shares'], '20.0000')
        self.assertEqual(res['additional_investment'], '800.00')

    def test_reprice_by_shares_negative_input(self):
        position = {
            'current_shares': '-10.00',
            'average_price': '100.00',
            'market_price': '80.00'
        }
        with self.assertRaises(ValueError):
            calculate_reprice_by_shares(position, Decimal('10.00'))

    def test_reprice_by_target_average_down(self):
        position = {
            'current_shares': '10.00',
            'average_price': '100.00',
            'market_price': '80.00'
        }
        res = calculate_reprice_by_target(position, Decimal('90.00'))
        self.assertEqual(res['additional_shares_needed'], '10.0000')
        self.assertEqual(res['total_shares'], '20.0000')
        self.assertEqual(res['additional_investment'], '800.00')

    def test_reprice_by_target_impossible_down(self):
        position = {
            'current_shares': '10.00',
            'average_price': '100.00',
            'market_price': '95.00'
        }
        with self.assertRaisesRegex(ValueError, r"Target price.*must be higher than the market price.*"):
            calculate_reprice_by_target(position, Decimal('90.00'))

    def test_calculate_trade_scenario_valid(self):
        from calculators.reprice_engine import calculate_trade_scenario
        position = {
            'current_shares': '10.00',
            'average_price': '100.00',
            'market_price': '80.00'
        }
        tranches = [
            {'price': '70.00', 'investment_amount': '1400.00'},
            {'price': '60.00', 'investment_amount': '1200.00'}
        ]
        res = calculate_trade_scenario(position, tranches)
        
        # Initial: 10 sh @ $100 = $1000
        # Tranche 1: 20 sh @ $70 = $1400
        # Tranche 2: 20 sh @ $60 = $1200
        # Total Shares = 50
        # Total Cost = $3600
        # Final Avg = $72.00
        
        self.assertEqual(res['final_average_price'], '72.00')
        self.assertEqual(res['total_shares'], '50.0000')
        self.assertEqual(res['total_additional_investment'], '2600.00')
        self.assertEqual(res['lowest_price_reached'], '60.00')
        # Original break-even recovery: (100 - 60) / 60 = 40 / 60 = 66.67%
        self.assertEqual(res['original_recovery_percent'], '66.67')
        # New break-even recovery: (72 - 60) / 60 = 12 / 60 = 20.00%
        self.assertEqual(res['breakeven_recovery_percent'], '20.00')

if __name__ == '__main__':
    unittest.main()
