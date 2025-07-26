# portfolio/management/commands/populate_historical_data.py
from django.core.management.base import BaseCommand
from django.conf import settings
from portfolio.models import StockHolding, HistoricalPrice
import requests
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import time # For pausing to respect API limits

class Command(BaseCommand):
    help = 'Populates historical stock data for existing holdings from Alpha Vantage.'

    def handle(self, *args, **options):
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if not api_key:
            self.stdout.write(self.style.ERROR('Alpha Vantage API key not found in settings.'))
            self.stdout.write(self.style.ERROR('Please set ALPHA_VANTAGE_API_KEY in your .env file and load it in settings.py'))
            return

        # Get all unique stock symbols from user holdings
        # Using .values_list('stock_symbol', flat=True).distinct() is efficient
        unique_symbols = StockHolding.objects.values_list('stock_symbol', flat=True).distinct()

        if not unique_symbols:
            self.stdout.write(self.style.WARNING('No stock holdings found to populate historical data for.'))
            return

        self.stdout.write(self.style.SUCCESS(f"Attempting to fetch historical data for {len(unique_symbols)} unique symbols..."))

        # Alpha Vantage free tier limits: 5 calls/minute, 500 calls/day
        # We'll pause briefly between calls to stay within the minute limit
        request_count = 0
        MAX_REQUESTS_PER_MINUTE = 5
        SECONDS_BETWEEN_REQUESTS = 65 / MAX_REQUESTS_PER_MINUTE # 13 seconds for 5 req/min, give it a bit extra

        for symbol in unique_symbols:
            if request_count >= MAX_REQUESTS_PER_MINUTE:
                self.stdout.write(self.style.WARNING(f"Rate limit approaching. Pausing for {SECONDS_BETWEEN_REQUESTS:.1f} seconds..."))
                time.sleep(SECONDS_BETWEEN_REQUESTS)
                request_count = 0

            self.stdout.write(f"Fetching historical data for {symbol}...")
            # Using 'TIME_SERIES_DAILY' with 'outputsize=full' to get the last ~20 years of daily data
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}"

            try:
                response = requests.get(url)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                data = response.json()
                request_count += 1

                if "Error Message" in data:
                    self.stdout.write(self.style.ERROR(f"Alpha Vantage API Error for {symbol}: {data['Error Message']}"))
                    continue
                if "Note" in data:
                    self.stdout.write(self.style.WARNING(f"Alpha Vantage API Note for {symbol}: {data['Note']}"))
                    # If it's a rate limit note, we might still get some data, but handle accordingly.
                    # For now, we'll continue trying to parse.

                time_series = data.get("Time Series (Daily)")
                if not time_series:
                    self.stdout.write(self.style.WARNING(f"No daily time series data found for {symbol}. Skipping."))
                    continue

                for date_str, values in time_series.items():
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        close_price_str = values['4. close']
                        close_price = Decimal(close_price_str)

                        # Create or update the HistoricalPrice entry
                        # update_or_create is good for avoiding duplicates on subsequent runs
                        HistoricalPrice.objects.update_or_create(
                            stock_symbol=symbol,
                            date=date_obj,
                            defaults={'close_price': close_price}
                        )
                    except (ValueError, KeyError, InvalidOperation) as e:
                        self.stdout.write(self.style.ERROR(f"Error parsing data for {symbol} on {date_str}: {e}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An unexpected error occurred for {symbol} on {date_str}: {e}"))


                self.stdout.write(self.style.SUCCESS(f"Successfully processed historical data for {symbol}."))

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Network or API error fetching data for {symbol}: {e}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An unexpected error occurred during API call for {symbol}: {e}"))

        self.stdout.write(self.style.SUCCESS('Historical data population complete.'))