# portfolio/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class StockHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=10, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateField()

    # Caching fields for live price data
    last_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} shares of {self.stock_symbol} ({self.user.username})"

    class Meta:
        ordering = ['stock_symbol', 'purchase_date']
    
class PortfolioSnapshot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    total_value = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        # Ensure only one snapshot per user per day
        unique_together = ('user', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.user.username}'s Portfolio on {self.date}: ${self.total_value}"