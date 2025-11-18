# calculators/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SavedRepriceStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # The Position Snapshot
    current_shares = models.DecimalField(max_digits=19, decimal_places=4)
    average_price = models.DecimalField(max_digits=19, decimal_places=4)
    market_price = models.DecimalField(max_digits=19, decimal_places=4)
    
    # The Strategy Inputs
    strategy_mode = models.CharField(max_length=10, choices=[('shares', 'Shares'), ('price', 'Target Price')])
    strategy_value = models.DecimalField(max_digits=19, decimal_places=4)

    class Meta:
        ordering = ['-created_at'] # Newest first

    def __str__(self):
        return f"{self.name} ({self.user.username})"