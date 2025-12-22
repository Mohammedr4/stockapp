# calculators/serializers.py
from rest_framework import serializers
from .models import SavedRepriceStrategy, SavedCapitalGainsScenario, SavedRebalanceScenario

# GLOBAL SETTING: Max digits 30, Decimal places 10
# This ensures consistency and safety across all calculators.

class TransactionLotSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    quantity = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)
    price = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)
    fees = serializers.DecimalField(max_digits=30, decimal_places=10, required=False, default=0.00)

class TaxProfileSerializer(serializers.Serializer):
    jurisdiction = serializers.ChoiceField(choices=['UK', 'US'], required=True)
    annual_income = serializers.DecimalField(max_digits=30, decimal_places=2, required=True)
    filing_status = serializers.ChoiceField(choices=['single', 'married_jointly'], required=False)

class CapitalGainsRequestSerializer(serializers.Serializer):
    asset_name = serializers.CharField(max_length=100, required=True)
    purchase_lots = TransactionLotSerializer(many=True, required=True, allow_empty=False)
    sale = TransactionLotSerializer(required=True)
    tax_profile = TaxProfileSerializer(required=True)

# --- Reprice Serializers ---

class RepricePositionSerializer(serializers.Serializer):
    current_shares = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)
    average_price = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)
    market_price = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)

class RepriceStrategySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=['shares', 'price'], required=True)
    value = serializers.DecimalField(max_digits=30, decimal_places=10, required=True)

class RepriceRequestSerializer(serializers.Serializer):
    position = RepricePositionSerializer(required=True)
    strategy = RepriceStrategySerializer(required=True)

# --- Rebalance Serializers ---

class RebalanceHoldingSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    value = serializers.DecimalField(max_digits=30, decimal_places=2)
    category = serializers.CharField(max_length=100)

class RebalanceCategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    target = serializers.IntegerField(min_value=0, max_value=100)

class RebalanceRequestSerializer(serializers.Serializer):
    holdings = RebalanceHoldingSerializer(many=True, required=True)
    categories = RebalanceCategorySerializer(many=True, required=True)

# --- DB Model Serializers ---

class SavedRepriceStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedRepriceStrategy
        fields = ['id', 'name', 'created_at', 'current_shares', 'average_price', 'market_price', 'strategy_mode', 'strategy_value']
        read_only_fields = ['id', 'created_at']

class SavedCapitalGainsScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedCapitalGainsScenario
        fields = ['id', 'name', 'created_at', 'input_data', 'result_data']
        read_only_fields = ['id', 'created_at']

class SavedRebalanceScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedRebalanceScenario
        fields = ['id', 'name', 'created_at', 'holdings_data', 'categories_data']
        read_only_fields = ['id', 'created_at']