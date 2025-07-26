# portfolio/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class StockHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField(null=True, blank=True) # Good, this allows optional date

    def __str__(self):
        return f"{self.quantity} shares of {self.stock_symbol} ({self.user.username})"

    class Meta:
        # REMOVE the 'unique_together = ('user', 'stock_symbol')' line.
        # It's what's causing the error because it prevents multiple entries for the same stock.
        # You can optionally add an ordering here if you like, e.g.:
        ordering = ['stock_symbol', 'purchase_date'] # This will make your listings ordered by default

# --- NEW MODEL FOR HISTORICAL PRICES ---
class HistoricalPrice(models.Model):
    stock_symbol = models.CharField(max_length=10)
    date = models.DateField() # Field is named 'date'
    close_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        # Ensure that for each stock symbol, there's only one price per day
        unique_together = ('stock_symbol', 'date') # <--- CHANGE THIS from 'purchase_date' to 'date'
        ordering = ['date'] # Order by date by default

    def __str__(self):
        return f"{self.stock_symbol} on {self.date}: ${self.close_price}"