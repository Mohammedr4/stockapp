# calculators/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SavedRepriceStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    current_shares = models.DecimalField(max_digits=19, decimal_places=4)
    average_price = models.DecimalField(max_digits=19, decimal_places=4)
    market_price = models.DecimalField(max_digits=19, decimal_places=4)
    
    # The Strategy Inputs
    strategy_mode = models.CharField(max_length=10, choices=[('shares', 'Shares'), ('price', 'Target Price'), ('tranches', 'Simulator')])
    strategy_value = models.TextField()  # Stores a decimal string for shares/price, or a JSON string for tranches

    class Meta:
        ordering = ['-created_at'] # Newest first

    def __str__(self):
        return f"{self.name} ({self.user.username})"

# --- Capital Gains Clarity Normalized Models ---

class SavedCapitalGainsScenario(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cgs_scenarios')
    name = models.CharField(max_length=100)
    asset_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - Tax Scenario ({self.user.username})"

class CGSPurchaseLot(models.Model):
    scenario = models.ForeignKey(SavedCapitalGainsScenario, related_name='purchase_lots', on_delete=models.CASCADE)
    date = models.DateField()
    quantity = models.DecimalField(max_digits=19, decimal_places=4)
    price = models.DecimalField(max_digits=19, decimal_places=4)
    fees = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)

class CGSSaleDetails(models.Model):
    scenario = models.OneToOneField(SavedCapitalGainsScenario, related_name='sale_details', on_delete=models.CASCADE)
    date = models.DateField()
    quantity = models.DecimalField(max_digits=19, decimal_places=4)
    price = models.DecimalField(max_digits=19, decimal_places=4)
    fees = models.DecimalField(max_digits=19, decimal_places=4, default=0.00)

class CGSTaxProfile(models.Model):
    scenario = models.OneToOneField(SavedCapitalGainsScenario, related_name='tax_profile', on_delete=models.CASCADE)
    jurisdiction = models.CharField(max_length=10, choices=[('UK', 'UK'), ('US', 'US')])
    annual_income = models.DecimalField(max_digits=19, decimal_places=2)
    filing_status = models.CharField(max_length=20, null=True, blank=True)

class CGSResult(models.Model):
    scenario = models.OneToOneField(SavedCapitalGainsScenario, related_name='results', on_delete=models.CASCADE)
    gross_gain_loss = models.DecimalField(max_digits=19, decimal_places=2)
    total_sale_proceeds = models.DecimalField(max_digits=19, decimal_places=2)
    total_purchase_cost = models.DecimalField(max_digits=19, decimal_places=2)
    estimated_tax = models.DecimalField(max_digits=19, decimal_places=2)
    net_gain_loss = models.DecimalField(max_digits=19, decimal_places=2)
    holding_period = models.CharField(max_length=50)
    gain_loss_type = models.CharField(max_length=50)




# --- DRIP Projection Models ---

class SavedDRIPProjection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drip_projections')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # Inputs
    initial_principal = models.DecimalField(max_digits=19, decimal_places=2)
    annual_contribution = models.DecimalField(max_digits=19, decimal_places=2)
    dividend_yield_percent = models.DecimalField(max_digits=6, decimal_places=2)
    annual_appreciation_percent = models.DecimalField(max_digits=6, decimal_places=2)
    years_to_grow = models.IntegerField()

    # Key result (for library card display)
    final_balance = models.DecimalField(max_digits=19, decimal_places=2, default=0)
    total_dividends = models.DecimalField(max_digits=19, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - DRIP ({self.user.username})"
