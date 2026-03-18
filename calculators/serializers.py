# calculators/serializers.py
from rest_framework import serializers
from .models import (
    SavedRepriceStrategy, 
    SavedCapitalGainsScenario, 
    CGSPurchaseLot,
    CGSSaleDetails,
    CGSTaxProfile,
    CGSResult
)
# GLOBAL SETTING: Max digits 19, Decimal places 4 (or 2 for currency)
# This mathematically aligns with the normalized database constraints to prevent silent truncation/crash on write.

class TransactionLotSerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    quantity = serializers.DecimalField(max_digits=19, decimal_places=4, required=True)
    price = serializers.DecimalField(max_digits=19, decimal_places=4, required=True)
    fees = serializers.DecimalField(max_digits=19, decimal_places=4, required=False, default=0.00)

class TaxProfileSerializer(serializers.Serializer):
    jurisdiction = serializers.ChoiceField(choices=['UK', 'US'], required=True)
    annual_income = serializers.DecimalField(max_digits=19, decimal_places=2, required=True)
    filing_status = serializers.ChoiceField(choices=['single', 'married_jointly'], required=False)

class CapitalGainsRequestSerializer(serializers.Serializer):
    asset_name = serializers.CharField(max_length=100, required=True)
    purchase_lots = TransactionLotSerializer(many=True, required=True, allow_empty=False)
    sale = TransactionLotSerializer(required=True)
    tax_profile = TaxProfileSerializer(required=True)

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

# --- Reprice Serializers ---

class RepricePositionSerializer(serializers.Serializer):
    current_shares = serializers.DecimalField(max_digits=19, decimal_places=4, required=True)
    average_price = serializers.DecimalField(max_digits=19, decimal_places=4, required=True)
    market_price = serializers.DecimalField(max_digits=19, decimal_places=4, required=True)

class TrancheSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=19, decimal_places=4, required=True, min_value=0.01)
    investment_amount = serializers.DecimalField(max_digits=19, decimal_places=2, required=True, min_value=0.01)

class RepriceStrategySerializer(serializers.Serializer):
    # Backward compatibility for the old UI, keep but make optional
    mode = serializers.ChoiceField(choices=['shares', 'price', 'tranches'], required=True)
    value = serializers.DecimalField(max_digits=19, decimal_places=4, required=False, allow_null=True)
    tranches = TrancheSerializer(many=True, required=False)

class RepriceRequestSerializer(serializers.Serializer):
    position = RepricePositionSerializer(required=True)
    strategy = RepriceStrategySerializer(required=True)

# --- DRIP Serializers ---

class DRIPRequestSerializer(serializers.Serializer):
    initial_principal = serializers.DecimalField(max_digits=19, decimal_places=2, required=True, min_value=0)
    annual_contribution = serializers.DecimalField(max_digits=19, decimal_places=2, required=True, min_value=0)
    dividend_yield_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=True, min_value=0)
    annual_appreciation_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=True, min_value=0)
    years_to_grow = serializers.IntegerField(required=True, min_value=1, max_value=50)

# --- DB Model Serializers ---

class SavedRepriceStrategySerializer(serializers.ModelSerializer):
    strategy_value = serializers.CharField()  # TextField: stores decimal string or JSON for tranches

    class Meta:
        model = SavedRepriceStrategy
        fields = ['id', 'name', 'created_at', 'current_shares', 'average_price', 'market_price', 'strategy_mode', 'strategy_value']
        read_only_fields = ['id', 'created_at']

# Capital Gains Relational Serializers
class CGSPurchaseLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CGSPurchaseLot
        fields = ['date', 'quantity', 'price', 'fees']

class CGSSaleDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CGSSaleDetails
        fields = ['date', 'quantity', 'price', 'fees']

class CGSTaxProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CGSTaxProfile
        fields = ['jurisdiction', 'annual_income', 'filing_status']

class CGSResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CGSResult
        fields = ['gross_gain_loss', 'total_sale_proceeds', 'total_purchase_cost', 'estimated_tax', 'net_gain_loss', 'holding_period', 'gain_loss_type']

class SavedCapitalGainsScenarioSerializer(serializers.ModelSerializer):
    input_data = serializers.SerializerMethodField()
    result_data = serializers.SerializerMethodField()

    class Meta:
        model = SavedCapitalGainsScenario
        fields = ['id', 'name', 'asset_name', 'created_at', 'input_data', 'result_data']
        read_only_fields = ['id', 'created_at']
        
    def get_input_data(self, obj):
        purchase_lots = CGSPurchaseLotSerializer(obj.purchase_lots.all(), many=True).data
        sale = None
        tax_profile = None
        try:
            sale = CGSSaleDetailsSerializer(obj.sale_details).data
        except Exception:
            pass
        try:
            tax_profile = CGSTaxProfileSerializer(obj.tax_profile).data
        except Exception:
            pass
        return {
            'asset_name': obj.asset_name,
            'purchase_lots': purchase_lots,
            'sale': sale,
            'tax_profile': tax_profile
        }
        
    def get_result_data(self, obj):
        try:
            res = CGSResultSerializer(obj.results).data
            return {
                "results": {
                    "gross_gain_loss": str(res['gross_gain_loss']),
                    "total_sale_proceeds": str(res['total_sale_proceeds']),
                    "total_purchase_cost": str(res['total_purchase_cost']),
                    "estimated_tax": str(res['estimated_tax']),
                    "net_gain_loss": str(res['net_gain_loss']),
                },
                "summary": {
                    "asset_name": obj.asset_name,
                    "jurisdiction": obj.tax_profile.jurisdiction if obj.tax_profile else '',
                    "holding_period": res['holding_period'],
                    "gain_loss_type": res['gain_loss_type'],
                }
            }
        except Exception:
            return {}

    def create(self, validated_data):
        # The view will pass the raw request data via context
        request_data = self.context.get('request').data
        
        scenario = SavedCapitalGainsScenario.objects.create(
            user=validated_data['user'], 
            name=request_data.get('name'),
            asset_name=request_data.get('input_data', {}).get('asset_name', 'Asset')
        )
        
        input_data = request_data.get('input_data', {})
        for lot in input_data.get('purchase_lots', []):
            CGSPurchaseLot.objects.create(scenario=scenario, **lot)
            
        CGSSaleDetails.objects.create(scenario=scenario, **input_data.get('sale', {}))
        CGSTaxProfile.objects.create(scenario=scenario, **input_data.get('tax_profile', {}))
        
        results_data = request_data.get('result_data', {})
        CGSResult.objects.create(
            scenario=scenario,
            gross_gain_loss=results_data.get('results', {}).get('gross_gain_loss', 0),
            total_sale_proceeds=results_data.get('results', {}).get('total_sale_proceeds', 0),
            total_purchase_cost=results_data.get('results', {}).get('total_purchase_cost', 0),
            estimated_tax=results_data.get('results', {}).get('estimated_tax', 0),
            net_gain_loss=results_data.get('results', {}).get('net_gain_loss', 0),
            holding_period=results_data.get('summary', {}).get('holding_period', ''),
            gain_loss_type=results_data.get('summary', {}).get('gain_loss_type', '')
        )
        return scenario

