# calculators/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SavedRepriceStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Updated to max_digits=30 to match your new "watertight" serializers
    current_shares = models.DecimalField(max_digits=30, decimal_places=10)
    average_price = models.DecimalField(max_digits=30, decimal_places=10)
    market_price = models.DecimalField(max_digits=30, decimal_places=10)
    
    # The Strategy Inputs
    strategy_mode = models.CharField(max_length=10, choices=[('shares', 'Shares'), ('price', 'Target Price')])
    strategy_value = models.DecimalField(max_digits=30, decimal_places=10)

    class Meta:
        ordering = ['-created_at'] # Newest first

    def __str__(self):
        return f"{self.name} ({self.user.username})"

class SavedCapitalGainsScenario(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We use JSONField to store the variable list of purchase lots and the results
    input_data = models.JSONField() 
    result_data = models.JSONField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - Tax Scenario ({self.user.username})"
    
class SavedRebalanceScenario(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We store the rows as JSON because they are flexible lists
    # Structure: [{'symbol': 'AAPL', 'value': '100', 'category': 'US Stocks'}]
    holdings_data = models.JSONField(default=list) 
    
    # Structure: [{'name': 'US Stocks', 'target': 60}]
    categories_data = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} - {self.user.username}"