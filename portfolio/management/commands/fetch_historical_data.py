# portfolio/management/commands/fetch_historical_data.py
import os
import requests
from django.core.management.base import BaseCommand
from portfolio.models import HistoricalPrice
from django.conf import settings
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

class Command(BaseCommand):
    help = 'Fetches historical stock prices from Alpha Vantage and stores them.'

    def add_arguments(self, parser):
        parser.add_argument('symbols', nargs='*', type=str,
                            help='Space-separated stock symbols (e.g., AAPL MSFT GOOG).')
        parser.add_argument('--days', type=int, default=365,
                            help='Number of past days to fetch data for. Default is 365.')

    def handle(self, *args, **options):
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR("ALPHA_VANTAGE_API_KEY not found in settings."))
            return

        symbols_to_fetch = options['symbols']
        if not symbols_to_fetch:
            # If no symbols provided, fetch for all symbols in StockHolding
            from portfolio.models import StockHolding
            symbols_to_fetch = StockHolding.objects.values_list('stock_symbol', flat=True).distinct()
            if not symbols_to_fetch:
                self.stdout.write(self.style.WARNING("No stock symbols provided and no existing holdings found."))
                return

        days_to_fetch = options['days']

        self.stdout.write(self.style.SUCCESS(f"Fetching historical data for {', '.join(symbols_to_fetch)}..."))

        for symbol in symbols_to_fetch:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=compact&apikey={api_key}"
            try:
                response = requests.get(url)
                response.raise_for_status() # Raise an exception for HTTP errors
                data = response.json()

                if "Time Series (Daily)" in data:
                    time_series = data["Time Series (Daily)"]
                    fetched_count = 0
                    for date_str, values in time_series.items():
                        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        # Only fetch for the last 'days_to_fetch'
                        if current_date < datetime.now().date() - timedelta(days=days_to_fetch):
                            continue

                        try:
                            close_price = Decimal(values['4. close'])
                        except InvalidOperation:
                            self.stdout.write(self.style.WARNING(f"Invalid price for {symbol} on {date_str}: {values['4. close']}"))
                            continue

                        # Create or update the HistoricalPrice entry
                        HistoricalPrice.objects.update_or_create(
                            stock_symbol=symbol,
                            date=current_date,
                            defaults={'close_price': close_price}
                        )
                        fetched_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Successfully fetched and saved {fetched_count} historical prices for {symbol}."))
                elif "Error Message" in data:
                    self.stdout.write(self.style.ERROR(f"API Error for {symbol}: {data['Error Message']}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Unexpected API response for {symbol}: {data}"))

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network error fetching {symbol}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An unexpected error occurred for {symbol}: {e}"))