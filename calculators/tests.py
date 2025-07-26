# calculators/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from datetime import date
import json # For handling session data in view tests

# Import your forms and helper functions
from .forms import CapitalGainsForm, StockRepriceForm
from .views import calculate_holding_period, get_gain_loss_type, calculate_uk_cgt, calculate_us_cgt

class CapitalGainsFormTests(TestCase):
    """
    Tests for the CapitalGainsForm to ensure proper validation
    of various input scenarios.
    """

    def test_valid_data_uk(self):
        """
        Test form with valid data for UK jurisdiction.
        """
        form_data = {
            'asset_name': 'AAPL',
            'tax_rule_country': 'UK',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 100,
            'shares_sold': 100,
            'purchase_price_per_share': Decimal('150.00'),
            'sale_price_per_share': Decimal('170.00'),
            'commission_purchase': Decimal('5.00'),
            'commission_sale': Decimal('5.00'),
            'annual_taxable_income': Decimal('30000.00'), # Required for UK
            'us_filing_status': '', # Not required for UK
        }
        form = CapitalGainsForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form should be valid for UK data. Errors: {form.errors}")
        # Verify cleaned data types
        self.assertIsInstance(form.cleaned_data['shares_purchased'], int)
        self.assertIsInstance(form.cleaned_data['purchase_price_per_share'], Decimal)
        self.assertIsInstance(form.cleaned_data['purchase_date'], date)

    def test_valid_data_us(self):
        """
        Test form with valid data for US jurisdiction.
        """
        form_data = {
            'asset_name': 'GOOG',
            'tax_rule_country': 'US',
            'purchase_date': '2023-06-15',
            'sale_date': '2024-07-20',
            'shares_purchased': 50,
            'shares_sold': 50,
            'purchase_price_per_share': Decimal('1000.00'),
            'sale_price_per_share': Decimal('1200.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('75000.00'), # Required for US
            'us_filing_status': 'single', # Required for US
        }
        form = CapitalGainsForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form should be valid for US data. Errors: {form.errors}")

    def test_missing_required_fields(self):
        """
        Test form with missing required fields (e.g., shares_purchased, dates).
        """
        form_data = {
            'asset_name': 'MSFT',
            'tax_rule_country': 'UK',
            # Missing purchase_date, sale_date, shares_purchased, purchase_price_per_share, sale_price_per_share
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('40000.00'),
            'us_filing_status': '',
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('purchase_date', form.errors)
        self.assertIn('sale_date', form.errors)
        self.assertIn('shares_purchased', form.errors)
        self.assertIn('shares_sold', form.errors) # Ensure this is also checked
        self.assertIn('purchase_price_per_share', form.errors)
        self.assertIn('sale_price_per_share', form.errors)

    def test_sale_date_before_purchase_date(self):
        """
        Test custom validation for sale_date being before purchase_date.
        """
        form_data = {
            'asset_name': 'AMZN',
            'tax_rule_country': 'US',
            'purchase_date': '2024-01-01',
            'sale_date': '2023-12-31', # Invalid date
            'shares_purchased': 10,
            'shares_sold': 10,
            'purchase_price_per_share': Decimal('100.00'),
            'sale_price_per_share': Decimal('110.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('80000.00'),
            'us_filing_status': 'single',
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('sale_date', form.errors)
        self.assertEqual(form.errors['sale_date'][0], "Sale date cannot be before purchase date.")

    def test_shares_sold_exceeds_shares_purchased(self):
        """
        Test custom validation for shares_sold being greater than shares_purchased.
        """
        form_data = {
            'asset_name': 'NFLX',
            'tax_rule_country': 'US',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 50,
            'shares_sold': 60, # Invalid
            'purchase_price_per_share': Decimal('300.00'),
            'sale_price_per_share': Decimal('350.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('90000.00'),
            'us_filing_status': 'single',
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('shares_sold', form.errors)
        self.assertEqual(form.errors['shares_sold'][0], "Shares sold cannot exceed shares purchased for this specific transaction. For partial sales, please adjust shares purchased to match shares sold.")

    def test_uk_missing_annual_income(self):
        """
        Test UK jurisdiction validation when annual_taxable_income is missing.
        """
        form_data = {
            'asset_name': 'TSLA',
            'tax_rule_country': 'UK',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 10,
            'shares_sold': 10,
            'purchase_price_per_share': Decimal('200.00'),
            'sale_price_per_share': Decimal('250.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': '', # Missing
            'us_filing_status': '',
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('annual_taxable_income', form.errors)
        self.assertEqual(form.errors['annual_taxable_income'][0], "Please provide your annual taxable income for tax estimation.")

    def test_us_missing_filing_status(self):
        """
        Test US jurisdiction validation when filing_status is missing.
        """
        form_data = {
            'asset_name': 'NVDA',
            'tax_rule_country': 'US',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 5,
            'shares_sold': 5,
            'purchase_price_per_share': Decimal('500.00'),
            'sale_price_per_share': Decimal('600.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('100000.00'),
            'us_filing_status': '', # Missing
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('us_filing_status', form.errors)
        self.assertEqual(form.errors['us_filing_status'][0], "Please select your filing status for US tax estimation.")

    def test_us_missing_annual_income(self):
        """
        Test US jurisdiction validation when annual_taxable_income is missing.
        """
        form_data = {
            'asset_name': 'NVDA',
            'tax_rule_country': 'US',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 5,
            'shares_sold': 5,
            'purchase_price_per_share': Decimal('500.00'),
            'sale_price_per_share': Decimal('600.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': '', # Missing
            'us_filing_status': 'single',
        }
        form = CapitalGainsForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('annual_taxable_income', form.errors)
        self.assertEqual(form.errors['annual_taxable_income'][0], "Please provide your annual taxable income for tax estimation.")


class CapitalGainsHelperFunctionTests(TestCase):
    """
    Tests for the helper functions used in Capital Gains calculations.
    """

    def test_calculate_holding_period(self):
        """
        Test various scenarios for holding period calculation.
        """
        # Short-term
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), date(2023, 6, 30)), "5 month(s), 29 day(s)")
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), date(2023, 12, 31)), "11 month(s), 30 day(s)")
        # Long-term (exactly 1 year or more)
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), date(2024, 1, 1)), "1 year(s), 0 month(s), 0 day(s)")
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), date(2025, 3, 15)), "2 year(s), 2 month(s), 14 day(s)")
        # Same day / Invalid
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), date(2023, 1, 1)), "0 day(s)")
        self.assertEqual(calculate_holding_period(date(2023, 1, 5), date(2023, 1, 1)), "N/A") # Sale before purchase
        self.assertEqual(calculate_holding_period(None, date(2023, 1, 1)), "N/A")
        self.assertEqual(calculate_holding_period(date(2023, 1, 1), None), "N/A")

    def test_get_gain_loss_type(self):
        """
        Test determination of short-term vs. long-term gain/loss.
        """
        # Short-term (less than 1 year)
        self.assertEqual(get_gain_loss_type(date(2023, 1, 1), date(2023, 12, 31)), "Short-Term")
        self.assertEqual(get_gain_loss_type(date(2023, 6, 1), date(2024, 5, 31)), "Short-Term")
        # Long-term (1 year or more)
        self.assertEqual(get_gain_loss_type(date(2023, 1, 1), date(2024, 1, 1)), "Long-Term")
        self.assertEqual(get_gain_loss_type(date(2022, 1, 1), date(2024, 1, 1)), "Long-Term")
        # Edge cases
        self.assertEqual(get_gain_loss_type(date(2023, 1, 1), date(2023, 1, 1)), "Short-Term") # Same day is short-term
        self.assertEqual(get_gain_loss_type(None, date(2023, 1, 1)), "N/A")
        self.assertEqual(get_gain_loss_type(date(2023, 1, 1), None), "N/A")

    def test_calculate_uk_cgt(self):
        """
        Test UK Capital Gains Tax calculation with various scenarios.
        (Based on simplified 2024/2025 rules as implemented in views.py)
        """
        # No gain
        self.assertEqual(calculate_uk_cgt(Decimal('0.00'), Decimal('50000.00')), Decimal('0.00'))
        self.assertEqual(calculate_uk_cgt(Decimal('-100.00'), Decimal('50000.00')), Decimal('0.00'))

        # Gain below AEA (Annual Exempt Amount)
        self.assertEqual(calculate_uk_cgt(Decimal('2000.00'), Decimal('50000.00')), Decimal('0.00')) # AEA is 3000

        # Gain above AEA, entirely within basic rate band
        # Taxable gain = 5000 - 3000 = 2000. Tax = 2000 * 0.10 = 200
        self.assertEqual(calculate_uk_cgt(Decimal('5000.00'), Decimal('30000.00')), Decimal('200.00'))

        # Gain crossing basic and higher rate bands
        # Assume BASIC_RATE_THRESHOLD_UK is 50270.00
        # Scenario: Income 40000, Gain 20000
        # Taxable gain = 20000 - 3000 = 17000
        # Remaining basic rate band = 50270 - 40000 = 10270
        # 10270 @ 10% = 1027.00
        # Remaining gain = 17000 - 10270 = 6730
        # 6730 @ 20% = 1346.00
        # Total = 1027 + 1346 = 2373.00
        self.assertEqual(calculate_uk_cgt(Decimal('20000.00'), Decimal('40000.00')), Decimal('2373.00'))

        # High income, all gain in higher rate band
        # Assume income 60000, Gain 10000
        # Taxable gain = 10000 - 3000 = 7000
        # Income (60000) is already above basic rate threshold (50270).
        # So, all 7000 is taxed at 20% = 1400.00
        self.assertEqual(calculate_uk_cgt(Decimal('10000.00'), Decimal('60000.00')), Decimal('1400.00'))


    def test_calculate_us_cgt_short_term(self):
        """
        Test US Short-Term Capital Gains Tax calculation.
        (Based on simplified ordinary income rates as implemented in views.py)
        """
        # Short-term gain, low income (e.g., 10% bracket for total income)
        # Income 10000, Gain 5000. Total 15000. Falls into 0.12 rate bracket (threshold 11600)
        # Tax = 5000 * 0.12 = 600
        self.assertEqual(calculate_us_cgt(Decimal('5000.00'), Decimal('10000.00'), 'single', 'Short-Term'), Decimal('600.00'))

        # Short-term gain, higher income (e.g., 24% bracket for total income)
        # Income 100000, Gain 10000. Total 110000. Falls into 0.24 rate bracket (threshold 100000)
        # Tax = 10000 * 0.24 = 2400
        self.assertEqual(calculate_us_cgt(Decimal('10000.00'), Decimal('100000.00'), 'single', 'Short-Term'), Decimal('2400.00'))
        
        # No gain
        self.assertEqual(calculate_us_cgt(Decimal('0.00'), Decimal('50000.00'), 'single', 'Short-Term'), Decimal('0.00'))
        self.assertEqual(calculate_us_cgt(Decimal('-500.00'), Decimal('50000.00'), 'single', 'Short-Term'), Decimal('0.00'))


    def test_calculate_us_cgt_long_term(self):
        """
        Test US Long-Term Capital Gains Tax calculation.
        (Based on simplified LTCG brackets as implemented in views.py)
        """
        # Long-term gain, single filer
        # 0% bracket
        self.assertEqual(calculate_us_cgt(Decimal('10000.00'), Decimal('30000.00'), 'single', 'Long-Term'), Decimal('0.00')) # Total 40000 < 47025

        # 15% bracket
        self.assertEqual(calculate_us_cgt(Decimal('10000.00'), Decimal('40000.00'), 'single', 'Long-Term'), Decimal('1500.00')) # Total 50000 > 47025, so 15%
        self.assertEqual(calculate_us_cgt(Decimal('50000.00'), Decimal('200000.00'), 'single', 'Long-Term'), Decimal('7500.00')) # Total 250000, still in 15%

        # 20% bracket
        self.assertEqual(calculate_us_cgt(Decimal('100000.00'), Decimal('500000.00'), 'single', 'Long-Term'), Decimal('20000.00')) # Total 600000 > 518901, so 20%

        # Long-term gain, married jointly
        # 0% bracket
        self.assertEqual(calculate_us_cgt(Decimal('20000.00'), Decimal('70000.00'), 'married_jointly', 'Long-Term'), Decimal('0.00')) # Total 90000 < 94050

        # 15% bracket
        self.assertEqual(calculate_us_cgt(Decimal('20000.00'), Decimal('80000.00'), 'married_jointly', 'Long-Term'), Decimal('3000.00')) # Total 100000 > 94050, so 15%

        # 20% bracket
        self.assertEqual(calculate_us_cgt(Decimal('50000.00'), Decimal('550000.00'), 'married_jointly', 'Long-Term'), Decimal('10000.00')) # Total 600000 > 583751, so 20%


class CapitalGainsEstimatorViewTests(TestCase):
    """
    Tests for the capital_gains_estimator view, covering GET, POST,
    form validation, and session-based free use limits.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse('calculators:capital_gains_estimator')
        # Clear session before each test to ensure fresh state
        self.client.session.clear()

    def test_get_request_initial(self):
        """
        Test initial GET request to the calculator page.
        Should show an empty form and no results.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calculators/capital_gains_estimator.html')
        self.assertIsInstance(response.context['form'], CapitalGainsForm)
        self.assertFalse(response.context['results']['calculation_successful'])
        self.assertFalse(response.context['show_modal_for_signup'])
        self.assertTrue(response.context['calculation_allowed'])

    def test_get_request_free_use_limit_reached(self):
        """
        Test GET request when free use limit has been reached.
        Should block calculation and show signup modal.
        """
        session = self.client.session
        session['free_cgt_uses_count'] = 1 # Set to limit
        session.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['calculation_allowed'])
        self.assertTrue(response.context['show_modal_for_signup'])
        self.assertContains(response, "You've used your free Capital Gains calculation. Please log in or sign up for unlimited access!")

    def test_post_request_valid_data_uk(self):
        """
        Test POST request with valid UK data, expecting a redirect and results.
        """
        form_data = {
            'asset_name': 'TESTUK',
            'tax_rule_country': 'UK',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 100,
            'shares_sold': 100,
            'purchase_price_per_share': Decimal('10.00'),
            'sale_price_per_share': Decimal('20.00'),
            'commission_purchase': Decimal('1.00'),
            'commission_sale': Decimal('1.00'),
            'annual_taxable_income': Decimal('30000.00'),
            'us_filing_status': '',
        }
        response = self.client.post(self.url, data=form_data)
        
        # Expect a redirect to the same URL with an anchor
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(self.url))
        self.assertIn('#capital-gains-summary', response.url)

        # Follow the redirect to check the final page state
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['results']['calculation_successful'])
        self.assertEqual(response.context['results']['asset_name'], 'TESTUK')
        self.assertEqual(response.context['results']['gross_gain_loss'], Decimal('998.00')) # (2000-1) - (1000+1) = 998
        self.assertEqual(response.context['results']['tax_currency'], '£')
        self.assertGreater(self.client.session.get('free_cgt_uses_count', 0), 0) # Check free use count increased

    def test_post_request_invalid_data(self):
        """
        Test POST request with invalid data, expecting form errors and no results.
        """
        form_data = {
            'asset_name': 'INVALID',
            'tax_rule_country': 'US',
            'purchase_date': '2024-01-01',
            'sale_date': '2023-12-31', # Invalid: sale date before purchase date
            'shares_purchased': 10,
            'shares_sold': 10,
            'purchase_price_per_share': Decimal('100.00'),
            'sale_price_per_share': Decimal('110.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('80000.00'),
            'us_filing_status': 'single',
        }
        response = self.client.post(self.url, data=form_data)
        
        # Should render the same page with form errors, not redirect
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('sale_date', response.context['form'].errors)
        self.assertFalse(response.context['results']['calculation_successful'])
        self.assertEqual(self.client.session.get('free_cgt_uses_count', 0), 0) # Free use count should NOT increase for invalid submission

    def test_post_request_free_use_limit_reached(self):
        """
        Test POST request when free use limit has been reached.
        Should block calculation and show signup modal.
        """
        session = self.client.session
        session['free_cgt_uses_count'] = 1 # Set to limit
        session.save()

        form_data = {
            'asset_name': 'BLOCKED',
            'tax_rule_country': 'US',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 10,
            'shares_sold': 10,
            'purchase_price_per_share': Decimal('100.00'),
            'sale_price_per_share': Decimal('110.00'),
            'commission_purchase': Decimal('0.00'),
            'commission_sale': Decimal('0.00'),
            'annual_taxable_income': Decimal('80000.00'),
            'us_filing_status': 'single',
        }
        response = self.client.post(self.url, data=form_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['calculation_allowed'])
        self.assertTrue(response.context['show_modal_for_signup'])
        self.assertContains(response, "You've used your free Capital Gains calculation. Please log in or sign up for unlimited access!")
        self.assertEqual(self.client.session.get('free_cgt_uses_count', 0), 1) # Should remain at limit, not increment further

    def test_post_redirect_get_preserves_data(self):
        """
        Test that form data and results are preserved across a POST-redirect-GET cycle.
        """
        form_data = {
            'asset_name': 'PERSIST',
            'tax_rule_country': 'US',
            'purchase_date': '2023-01-01',
            'sale_date': '2024-01-01',
            'shares_purchased': 10,
            'shares_sold': 10,
            'purchase_price_per_share': Decimal('100.00'),
            'sale_price_per_share': Decimal('150.00'),
            'commission_purchase': Decimal('2.00'),
            'commission_sale': Decimal('3.00'),
            'annual_taxable_income': Decimal('100000.00'),
            'us_filing_status': 'single',
        }
        
        # First POST request
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302) # Expect redirect

        # Follow the redirect
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)

        # Check if form fields are pre-populated
        self.assertEqual(response.context['form']['asset_name'].value(), 'PERSIST')
        self.assertEqual(response.context['form']['shares_purchased'].value(), 10)
        self.assertEqual(response.context['form']['purchase_date'].value(), date(2023, 1, 1))

        # Check if results are displayed correctly
        self.assertTrue(response.context['results']['calculation_successful'])
        self.assertEqual(response.context['results']['gross_gain_loss'], Decimal('495.00')) # (150*10 - 3) - (100*10 + 2) = 1497 - 1002 = 495
        self.assertEqual(response.context['results']['tax_currency'], '$')
        self.assertEqual(response.context['results']['holding_period'], '1 year(s), 0 month(s), 0 day(s)')


class StockRepriceFormTests(TestCase):
    """
    Basic tests for StockRepriceForm.
    (Can be expanded similar to CapitalGainsFormTests)
    """

    def test_valid_data_shares_mode(self):
        form_data = {
            'stock_symbol': 'XYZ',
            'current_shares': 100,
            'average_buy_price': Decimal('50.00'),
            'current_market_price': Decimal('60.00'),
            'calculation_mode': 'shares',
            'additional_shares_to_buy': 50,
            'target_average_price': '', # Should be ignored
        }
        form = StockRepriceForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form should be valid for shares mode. Errors: {form.errors}")

    def test_valid_data_price_mode(self):
        form_data = {
            'stock_symbol': 'ABC',
            'current_shares': 100,
            'average_buy_price': Decimal('50.00'),
            'current_market_price': Decimal('40.00'),
            'calculation_mode': 'price',
            'additional_shares_to_buy': '', # Should be ignored
            'target_average_price': Decimal('45.00'),
        }
        form = StockRepriceForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form should be valid for price mode. Errors: {form.errors}")

    def test_invalid_data_missing_mode_field(self):
        """
        Test that the correct field is required based on calculation mode.
        """
        # Shares mode, but missing additional_shares_to_buy
        form_data = {
            'stock_symbol': 'XYZ',
            'current_shares': 100,
            'average_buy_price': Decimal('50.00'),
            'current_market_price': Decimal('60.00'),
            'calculation_mode': 'shares',
            'additional_shares_to_buy': '', # Missing
            'target_average_price': '',
        }
        form = StockRepriceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('additional_shares_to_buy', form.errors)

        # Price mode, but missing target_average_price
        form_data = {
            'stock_symbol': 'ABC',
            'current_shares': 100,
            'average_buy_price': Decimal('50.00'),
            'current_market_price': Decimal('40.00'),
            'calculation_mode': 'price',
            'additional_shares_to_buy': '',
            'target_average_price': '', # Missing
        }
        form = StockRepriceForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('target_average_price', form.errors)