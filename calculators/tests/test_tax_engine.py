import unittest
from decimal import Decimal
from datetime import date
from calculators.tax_engine import calculate_fifo_cost_basis, get_holding_period_and_type

class TestTaxEngine(unittest.TestCase):
    def test_fifo_cost_basis_simple(self):
        lots = [
            {'date': date(2023, 1, 1), 'quantity': Decimal('100'), 'price': Decimal('10.00'), 'fees': Decimal('5.00')},
            {'date': date(2023, 2, 1), 'quantity': Decimal('100'), 'price': Decimal('20.00'), 'fees': Decimal('5.00')},
        ]
        # Sell 150 shares
        basis, fees = calculate_fifo_cost_basis(lots, Decimal('150'))
        
        # Should take 100 shares @ $10, and 50 shares @ $20
        expected_basis = (Decimal('100') * Decimal('10.00')) + (Decimal('50') * Decimal('20.00'))
        self.assertEqual(basis, expected_basis)
        
        # Fees should be 100% of first lot, 50% of second
        expected_fees = Decimal('5.00') + Decimal('2.50')
        self.assertEqual(fees, expected_fees)

    def test_fifo_oversell_error(self):
        lots = [
            {'date': date(2023, 1, 1), 'quantity': Decimal('100'), 'price': Decimal('10.00'), 'fees': Decimal('5.00')},
        ]
        with self.assertRaisesMessage(ValueError, "Sale quantity.*exceeds total owned quantity.*"):
            calculate_fifo_cost_basis(lots, Decimal('150'))

    def test_holding_period_long_term_strict(self):
        purchase = date(2023, 1, 1)
        # Exactly one year later is still Short-Term under U.S. rules!
        sale_exact_year = date(2024, 1, 1)
        _, type_exact = get_holding_period_and_type(purchase, sale_exact_year)
        self.assertEqual(type_exact, "Short-Term")
        
        # One year and one day later is Long-Term
        sale_long = date(2024, 1, 2)
        _, type_long = get_holding_period_and_type(purchase, sale_long)
        self.assertEqual(type_long, "Long-Term")

if __name__ == '__main__':
    unittest.main()
