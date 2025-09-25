# portfolio/views.py
from rest_framework import status
from .serializers import StockHoldingSerializer
import os
import requests
import time
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import StockHolding, PortfolioSnapshot
from calculators.views import get_alpha_vantage_data # Reusing our helper

from datetime import timedelta

@login_required
def portfolio_dashboard_view(request):
    """ Renders the new portfolio dashboard. """
    return render(request, 'portfolio/dashboard.html')

class PortfolioAPIView(APIView):
    """
    Provides a complete summary of the user's portfolio, including
    live prices, overall metrics, and historical performance data.
    """
    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        holdings = StockHolding.objects.filter(user=user)
        snapshots = PortfolioSnapshot.objects.filter(user=user).order_by('date')

        total_portfolio_value = Decimal('0.00')
        total_investment = Decimal('0.00')
        holdings_data = []

        for holding in holdings:
            cost_basis = holding.quantity * holding.purchase_price
            total_investment += cost_basis
            
            current_price = holding.last_price
            if not holding.last_updated or holding.last_updated < timezone.now() - timedelta(minutes=15):
                api_data = get_alpha_vantage_data(holding.stock_symbol, 'GLOBAL_QUOTE')
                if 'Global Quote' in api_data and api_data.get('Global Quote'):
                    try:
                        current_price = Decimal(api_data['Global Quote']['05. price'])
                        holding.last_price = current_price
                        holding.last_updated = timezone.now()
                        holding.save()
                        time.sleep(15)
                    except (KeyError, ValueError):
                        pass
            
            market_value = holding.quantity * current_price if current_price is not None else Decimal('0.00')
            total_portfolio_value += market_value
            pnl = market_value - cost_basis if current_price is not None else Decimal('0.00')

            holdings_data.append({
                'id': holding.id,
                'symbol': holding.stock_symbol,
                'quantity': f"{holding.quantity:.4f}",
                'average_price': f"{holding.purchase_price:.2f}",
                'cost_basis': f"{cost_basis:.2f}",
                'market_price': f"{current_price:.2f}" if current_price is not None else "N/A",
                'market_value': f"{market_value:.2f}",
                'pnl_amount': f"{pnl:.2f}",
                'pnl_percent': f"{(pnl / cost_basis * 100):.2f}" if cost_basis > 0 else "0.00",
                'allocation': f"{(market_value / total_portfolio_value * 100):.2f}" if total_portfolio_value > 0 else "0.00",
                'purchase_date': holding.purchase_date.strftime('%Y-%m-%d') if holding.purchase_date else None,
            })

        overall_pnl = total_portfolio_value - total_investment
        overall_pnl_percent = (overall_pnl / total_investment * 100) if total_investment > 0 else Decimal('0.00')

        chart_labels = [s.date.strftime('%Y-%m-%d') for s in snapshots]
        chart_values = [float(s.total_value) for s in snapshots]

        response_data = {
            'summary': {
                'total_value': f"{total_portfolio_value:.2f}",
                'total_investment': f"{total_investment:.2f}",
                'overall_pnl': f"{overall_pnl:.2f}",
                'overall_pnl_percent': f"{overall_pnl_percent:.2f}",
            },
            'holdings': holdings_data,
            'chart_data': { 'labels': chart_labels, 'values': chart_values }
        }
        return Response(response_data)

class StockHoldingAPIView(APIView):
    """ Handles CRUD (Create, Read, Update, Delete) for StockHoldings. """
    def post(self, request, *args, **kwargs):
        """ Create a new stock holding. """
        serializer = StockHoldingSerializer(data=request.data)
        if serializer.is_valid():
            # Associate the holding with the logged-in user before saving
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, *args, **kwargs):
        """ Update an existing stock holding. """
        try:
            holding = StockHolding.objects.get(pk=pk, user=request.user)
        except StockHolding.DoesNotExist:
            return Response({'error': 'Holding not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = StockHoldingSerializer(holding, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        """ Delete a stock holding. """
        try:
            holding = StockHolding.objects.get(pk=pk, user=request.user)
        except StockHolding.DoesNotExist:
            return Response({'error': 'Holding not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        holding.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)