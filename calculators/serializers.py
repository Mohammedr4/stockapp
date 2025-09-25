# calculators/serializers.py
from rest_framework import serializers

class TransactionLotSerializer(serializers.Serializer):
    """Defines a single purchase or sale event."""
    date = serializers.DateField(required=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=4, required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    fees = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.00)

class TaxProfileSerializer(serializers.Serializer):
    """Defines the user's tax situation."""
    jurisdiction = serializers.ChoiceField(choices=['UK', 'US'], required=True)
    annual_income = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    filing_status = serializers.ChoiceField(
        choices=['single', 'married_jointly'], 
        required=False # Only required for US
    )

class CapitalGainsRequestSerializer(serializers.Serializer):
    """The main serializer for the entire API request."""
    asset_name = serializers.CharField(max_length=100, required=True)
    purchase_lots = TransactionLotSerializer(many=True, required=True, allow_empty=False)
    sale = TransactionLotSerializer(required=True)
    tax_profile = TaxProfileSerializer(required=True)

# --- Serializers for the Repricing Strategy Dashboard ---

class RepricePositionSerializer(serializers.Serializer):
    """Defines the user's current stock position."""
    current_shares = serializers.DecimalField(max_digits=12, decimal_places=4, required=True)
    average_price = serializers.DecimalField(max_digits=12, decimal_places=4, required=True)
    market_price = serializers.DecimalField(max_digits=12, decimal_places=4, required=True)

class RepriceStrategySerializer(serializers.Serializer):
    """Defines the user's strategic goal."""
    mode = serializers.ChoiceField(choices=['shares', 'price'], required=True)
    value = serializers.DecimalField(max_digits=12, decimal_places=4, required=True)

class RepriceRequestSerializer(serializers.Serializer):
    """The main serializer for the entire reprice API request."""
    position = RepricePositionSerializer(required=True)
    strategy = RepriceStrategySerializer(required=True)

class RebalanceHoldingSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    value = serializers.DecimalField(max_digits=12, decimal_places=2)
    category = serializers.CharField(max_length=100)

class RebalanceCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    target = serializers.IntegerField(min_value=0, max_value=100)

class RebalanceRequestSerializer(serializers.Serializer):
    holdings = RebalanceHoldingSerializer(many=True, required=True)
    categories = RebalanceCategorySerializer(many=True, required=True)