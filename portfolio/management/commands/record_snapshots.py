# portfolio/management/commands/record_snapshots.py
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

# Import the necessary models and our API helper function
from portfolio.models import StockHolding, PortfolioSnapshot
from calculators.views import get_alpha_vantage_data

from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Records a daily snapshot of the total value for each user portfolio.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting portfolio snapshot process...'))

        users = User.objects.all()
        today = timezone.now().date()

        for user in users:
            self.stdout.write(f"Processing portfolio for {user.username}...")
            
            # Check if a snapshot for today already exists for this user
            if PortfolioSnapshot.objects.filter(user=user, date=today).exists():
                self.stdout.write(self.style.WARNING(f'Snapshot for {user.username} on {today} already exists. Skipping.'))
                continue

            holdings = StockHolding.objects.filter(user=user)
            if not holdings:
                self.stdout.write(f'No holdings found for {user.username}. Skipping.')
                continue

            total_portfolio_value = Decimal('0.00')
            
            # To respect API limits, we cache prices we've already fetched in this run
            price_cache = {}

            for holding in holdings:
                symbol = holding.stock_symbol
                
                if symbol in price_cache:
                    current_price = price_cache[symbol]
                else:
                    # We need the 'Global Quote' for the most recent price
                    api_data = get_alpha_vantage_data(symbol, 'GLOBAL_QUOTE')
                    
                    if 'error' in api_data or 'Global Quote' not in api_data or not api_data['Global Quote']:
                        self.stdout.write(self.style.ERROR(f'Could not fetch price for {symbol}. Skipping holding.'))
                        price_cache[symbol] = None # Cache the failure to avoid re-querying
                        continue
                    
                    try:
                        current_price = Decimal(api_data['Global Quote']['05. price'])
                        price_cache[symbol] = current_price
                        # Alpha Vantage free tier has a limit of 5 calls per minute. We must wait.
                        time.sleep(15) # Wait 15 seconds between API calls
                    except (KeyError, ValueError):
                        self.stdout.write(self.style.ERROR(f'Invalid price data for {symbol}. Skipping holding.'))
                        price_cache[symbol] = None
                        continue
                
                if current_price is not None:
                    total_portfolio_value += holding.quantity * current_price

            # Create the new snapshot record
            PortfolioSnapshot.objects.create(
                user=user,
                date=today,
                total_value=total_portfolio_value
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully recorded snapshot for {user.username}: ${total_portfolio_value:.2f}'))

        self.stdout.write(self.style.SUCCESS('Successfully completed portfolio snapshot process.'))