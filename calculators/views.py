# calculators/views.py

import os
import requests
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

# Serializer Imports
from .serializers import CapitalGainsRequestSerializer, RepriceRequestSerializer, RebalanceRequestSerializer

# Engine Imports
from .tax_engine import (
    calculate_fifo_cost_basis,
    get_holding_period_and_type,
    calculate_uk_cgt,
    calculate_us_cgt
)
from .reprice_engine import calculate_reprice_by_shares, calculate_reprice_by_target


# --- Page Views ---

@login_required
def calculators_index(request):
    """ Renders the main index page for all calculators. """
    calculators = [
        {
            'name': 'Repricing Strategy Console',
            'description': 'An interactive workspace to model your stock positions and strategies.',
            'url_name': 'calculators:stock_reprice_calculator',
            'icon': 'fas fa-sync-alt'
        },
        {
            'name': 'Capital Gains Clarity Dashboard',
            'description': 'A step-by-step tool to provide insight into your investment gains.',
            'url_name': 'calculators:clarity_dashboard',
            'icon': 'fas fa-chart-line'
        },
        {
            'name': 'Portfolio Rebalancing Console',
            'description': 'Define a target allocation and get an action plan to rebalance your portfolio.',
            'url_name': 'calculators:rebalance_dashboard',
            'icon': 'fas fa-balance-scale'
        }
    ]
    context = {
        'calculators': calculators,
    }
    return render(request, 'calculators/index.html', context)
def clarity_dashboard_view(request):
    """ Renders the template for the new Capital Gains Clarity Dashboard. """
    return render(request, 'calculators/clarity_dashboard.html')

def reprice_dashboard_view(request):
    """ Renders the template for the new Repricing Strategy Dashboard. """
    return render(request, 'calculators/reprice_dashboard.html')

def rebalance_dashboard_view(request):
    """ Renders the template for the new Portfolio Rebalancing Console. """
    return render(request, 'calculators/rebalance_dashboard.html')


# --- Helper function for Alpha Vantage API calls ---
def get_alpha_vantage_data(symbol, function):
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        return {'error': 'Alpha Vantage API key not found.'}
    
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&outputsize=full&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # --- THIS IS THE CORRECTED LOGIC ---
        # First, check for any kind of error or informational message from the API.
        if "Error Message" in data or "Note" in data or "Information" in data:
            error_message = data.get("Error Message", data.get("Note", data.get("Information", "API error.")))
            return {'error': error_message}
            
        # If there's no error, we assume the data is valid and return it.
        # The view that calls this function will be responsible for finding the data it needs.
        return data

    except requests.exceptions.RequestException as e:
        return {'error': f"Network error: {e}"}

# --- API Views ---

class CapitalGainsAPIView(APIView):
    """ The API endpoint for the Capital Gains Clarity Dashboard. """
    def post(self, request, *args, **kwargs):
        serializer = CapitalGainsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        purchase_lots = data['purchase_lots']
        sale_details = data['sale']
        tax_profile = data['tax_profile']
        jurisdiction = tax_profile['jurisdiction']
        annual_income = tax_profile['annual_income']

        try:
            sorted_lots = sorted(purchase_lots, key=lambda lot: lot['date'])
            cost_basis, fees_on_sold_shares = calculate_fifo_cost_basis(
                sorted_lots, sale_details['quantity']
            )
            first_purchase_date = sorted_lots[0]['date']
        except (ValueError, IndexError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        total_sale_proceeds = (sale_details['price'] * sale_details['quantity']) - sale_details['fees']
        total_purchase_cost = cost_basis + fees_on_sold_shares
        gross_gain_loss = total_sale_proceeds - total_purchase_cost
        
        holding_period, gain_type = get_holding_period_and_type(first_purchase_date, sale_details['date'])

        estimated_tax = Decimal('0.00')
        if jurisdiction == 'UK':
            estimated_tax = calculate_uk_cgt(gross_gain_loss, annual_income)
        elif jurisdiction == 'US':
            filing_status = tax_profile.get('filing_status')
            if not filing_status:
                return Response({'error': 'Filing status is required for US tax calculation.'}, status=status.HTTP_400_BAD_REQUEST)
            estimated_tax = calculate_us_cgt(gross_gain_loss, annual_income, filing_status, gain_type)

        net_gain_loss = gross_gain_loss - estimated_tax

        response_data = {
            "results": { "gross_gain_loss": f"{gross_gain_loss:.2f}", "total_sale_proceeds": f"{total_sale_proceeds:.2f}", "total_purchase_cost": f"{total_purchase_cost:.2f}", "estimated_tax": f"{estimated_tax:.2f}", "net_gain_loss": f"{net_gain_loss:.2f}", },
            "summary": { "asset_name": data['asset_name'], "jurisdiction": jurisdiction, "holding_period": holding_period, "gain_loss_type": gain_type, }
        }
        return Response(response_data, status=status.HTTP_200_OK)

class RepriceAPIView(APIView):
    """ The API endpoint for the Repricing Strategy Dashboard. """
    def post(self, request, *args, **kwargs):
        serializer = RepriceRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        position = data['position']
        strategy = data['strategy']
        
        try:
            if strategy['mode'] == 'shares':
                results = calculate_reprice_by_shares(position, strategy['value'])
            elif strategy['mode'] == 'price':
                results = calculate_reprice_by_target(position, strategy['value'])
            else:
                return Response({'error': 'Invalid strategy mode.'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(results, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RebalanceAPIView(APIView):
    """ The API endpoint for the Portfolio Rebalancing Console. """
    def post(self, request, *args, **kwargs):
        serializer = RebalanceRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        holdings = data['holdings']
        categories = data['categories']

        # 1. Calculate Total Portfolio Value
        total_portfolio_value = sum(h['value'] for h in holdings)
        if total_portfolio_value <= 0:
            return Response({'error': 'Portfolio value must be positive.'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Calculate Current Allocation
        current_allocation = {cat['name']: {'value': Decimal('0.00'), 'percent': Decimal('0.00')} for cat in categories}
        for h in holdings:
            if h['category'] in current_allocation: # Ensure the category exists
                current_allocation[h['category']]['value'] += h['value']
        
        for cat_name, values in current_allocation.items():
            # THIS LINE IS NOW CORRECTED
            values['percent'] = round((values['value'] / total_portfolio_value) * 100, 2)

        # 3. Calculate Target Allocation and Difference
        target_allocation = {cat['name']: {'value': Decimal('0.00'), 'percent': Decimal(cat['target'])} for cat in categories}
        orders = []
        for cat_name, values in target_allocation.items():
            values['value'] = total_portfolio_value * (values['percent'] / 100)
            difference = values['value'] - current_allocation[cat_name]['value']
            
            if difference > 0:
                action = 'BUY'
            elif difference < 0:
                action = 'SELL'
            else:
                action = 'HOLD'

            orders.append({
                'category': cat_name,
                'difference_value': f"{difference:.2f}",
                'action': action
            })

        # 4. Construct the Response
        response_data = {
            'total_portfolio_value': f"{total_portfolio_value:.2f}",
            'current_allocation': {k: { 'value': f"{v['value']:.2f}", 'percent': f"{v['percent']:.2f}" } for k, v in current_allocation.items()},
            'target_allocation': {k: { 'value': f"{v['value']:.2f}", 'percent': f"{v['percent']:.2f}" } for k, v in target_allocation.items()},
            'rebalancing_orders': orders
        }

        return Response(response_data, status=status.HTTP_200_OK)