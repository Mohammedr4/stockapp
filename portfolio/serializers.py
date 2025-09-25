# portfolio/serializers.py
from rest_framework import serializers
from .models import StockHolding

class StockHoldingSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockHolding
        fields = ['id', 'stock_symbol', 'quantity', 'purchase_price', 'purchase_date']
        read_only_fields = ['id']