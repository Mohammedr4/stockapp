# calculators/views.py
import io
import os
import requests
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from django.utils import timezone

# Serializer Imports
from .serializers import (
    CapitalGainsRequestSerializer, 
    RepriceRequestSerializer, 
    RebalanceRequestSerializer, 
    SavedRepriceStrategySerializer,
    SavedCapitalGainsScenarioSerializer,
    SavedRebalanceScenarioSerializer
)

# Model Imports
# This was the missing piece causing the NameError
from .models import SavedRepriceStrategy, SavedCapitalGainsScenario, SavedRebalanceScenario

# Engine Imports
from .tax_engine import (
    calculate_fifo_cost_basis,
    get_holding_period_and_type,
    calculate_uk_cgt,
    calculate_us_cgt
)
from .reprice_engine import calculate_reprice_by_shares, calculate_reprice_by_target

from .utils import render_to_pdf
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
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
        
        if "Error Message" in data or "Note" in data or "Information" in data:
            error_message = data.get("Error Message", data.get("Note", data.get("Information", "API error.")))
            if 'premium endpoint' in error_message.lower():
                return {'error': f'Historical dividend data for "{symbol}" is a premium feature and is currently unavailable.'}
            return {'error': error_message}
            
        if not data or "Time Series (Daily)" not in data:
            # For GLOBAL_QUOTE, the key is "Global Quote", not Time Series
            if function == 'GLOBAL_QUOTE' and 'Global Quote' in data:
                 return data
            elif function == 'TIME_SERIES_DAILY_ADJUSTED':
                 return data
            else:
                 return {'error': f'Invalid or empty response from API for symbol {symbol}.'}
            
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
            # PROFESSIONAL FIX: Extract the first validation error message
            error_data = serializer.errors
            first_key = next(iter(error_data))
            first_error_list = error_data[first_key]
            
            if isinstance(first_error_list, dict):
                first_error = next(iter(first_error_list.values()))[0]
            else:
                first_error = first_error_list[0]
            
            return Response({'error': first_error}, status=status.HTTP_400_BAD_REQUEST)

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

class SavedRepriceStrategyAPIView(APIView):
    """ Handles listing, creating, and deleting saved strategies. """
    
    def get(self, request, *args, **kwargs):
        """ List all saved strategies for the logged-in user. """
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        strategies = SavedRepriceStrategy.objects.filter(user=request.user)
        serializer = SavedRepriceStrategySerializer(strategies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ Save a new strategy. """
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = SavedRepriceStrategySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        """ Delete a specific strategy by ID. """
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            strategy = SavedRepriceStrategy.objects.get(pk=pk, user=request.user)
            strategy.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedRepriceStrategy.DoesNotExist:
            return Response({'error': 'Strategy not found'}, status=status.HTTP_404_NOT_FOUND)
    
class ExportRepricePDFView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        # Format data for the template
        context = {
            'data': {
                'current_shares': data.get('current_shares'),
                'average_price': data.get('average_price'),
                'market_price': data.get('market_price'),
                'strategy_name': "Buy Shares" if data.get('strategy_mode') == 'shares' else "Target Price",
                'strategy_desc': f"Value input: {data.get('strategy_value')}"
            },
            'results': {
                'New Average Price': f"${data.get('new_average_price', 'N/A')}",
                'Total Shares': data.get('total_shares', 'N/A'),
                'Additional Investment': f"${data.get('additional_investment', 'N/A')}"
            }
        }

        pdf = render_to_pdf('calculators/pdf_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"StockSavvy_Report.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return Response({'error': 'Failed to generate PDF'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class SavedCapitalGainsScenarioAPIView(APIView):
    """ Handles listing, creating, and deleting saved tax scenarios. """
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        scenarios = SavedCapitalGainsScenario.objects.filter(user=request.user)
        serializer = SavedCapitalGainsScenarioSerializer(scenarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = SavedCapitalGainsScenarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not request.user.is_authenticated:
             return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            scenario = SavedCapitalGainsScenario.objects.get(pk=pk, user=request.user)
            scenario.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedCapitalGainsScenario.DoesNotExist:
            return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)

class ExportCapitalGainsPDFView(APIView):
    """ Generates a PDF report for a capital gains calculation. """
    def post(self, request, *args, **kwargs):
        data = request.data
        
        # We expect the frontend to pass the full 'input_data' and 'result_data' structure
        # This matches how we save scenarios, making the data structure consistent.
        
        context = {
            'purchase_lots': data.get('purchase_lots', []),
            'sale': data.get('sale', {}),
            'results': data.get('results', {}),
            'summary': data.get('summary', {}),
        }
        
        pdf = render_to_pdf('calculators/pdf_capital_gains.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"TaxReport_{data.get('summary', {}).get('asset_name', 'Asset')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        return Response({'error': 'Failed to generate PDF'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class SavedRebalanceScenarioAPIView(APIView):
    """ Handles listing, creating, and deleting saved rebalance scenarios. """

    def get(self, request, *args, **kwargs):
        """ List all saved scenarios for the logged-in user. """
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        scenarios = SavedRebalanceScenario.objects.filter(user=request.user).order_by('-created_at')
        serializer = SavedRebalanceScenarioSerializer(scenarios, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """ Save a new scenario. """
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = SavedRebalanceScenarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        """ Delete a specific scenario. """
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            scenario = SavedRebalanceScenario.objects.get(pk=pk, user=request.user)
            scenario.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedRebalanceScenario.DoesNotExist:
            return Response({'error': 'Scenario not found'}, status=status.HTTP_404_NOT_FOUND)

class ExportRebalancePDFView(APIView):
    """
    Generates a PDF report for the Portfolio Rebalancing Calculator.
    Receives the calculation result JSON from the frontend.
    """
    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Create a file-like buffer to receive PDF data
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # 1. Header
        elements.append(Paragraph("Portfolio Rebalancing Plan", styles['Title']))
        elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # 2. Total Value
        total_value = data.get('total_portfolio_value', 0)
        elements.append(Paragraph(f"<b>Total Portfolio Value:</b> ${float(total_value):,.2f}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # 3. Allocation Summary Table
        elements.append(Paragraph("<b>Allocation Summary</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Table Header
        table_data = [['Category', 'Current %', 'Target %', 'Current $', 'Target $', 'Difference']]
        
        # Table Rows
        target_allocation = data.get('target_allocation', {})
        current_allocation = data.get('current_allocation', {})
        
        for category, target_info in target_allocation.items():
            current_info = current_allocation.get(category, {})
            
            # Format numbers
            curr_pct = f"{current_info.get('percent', 0)}%"
            tgt_pct = f"{target_info.get('percent', 0)}%"
            curr_val = f"${float(current_info.get('value', 0)):,.2f}"
            tgt_val = f"${float(target_info.get('value', 0)):,.2f}"
            
            # Calculate diff for display
            diff = float(target_info.get('value', 0)) - float(current_info.get('value', 0))
            diff_str = f"${diff:,.2f}"
            if diff > 0: diff_str = f"+{diff_str}"
            
            table_data.append([category, curr_pct, tgt_pct, curr_val, tgt_val, diff_str])

        # Draw Table 1
        t1 = Table(table_data)
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(t1)
        elements.append(Spacer(1, 20))

        # 4. Actionable Orders Table
        elements.append(Paragraph("<b>Actionable Orders</b>", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        orders_data = [['Action', 'Asset/Category', 'Amount']]
        rebalancing_orders = data.get('rebalancing_orders', [])
        
        for order in rebalancing_orders:
            if order['action'] == 'HOLD':
                continue
            
            amount = f"${abs(float(order['difference_value'])):,.2f}"
            orders_data.append([order['action'], order['category'], amount])
            
        if len(orders_data) > 1:
            t2 = Table(orders_data, colWidths=[100, 200, 100])
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(t2)
        else:
            elements.append(Paragraph("No trades needed. Your portfolio is balanced.", styles['Normal']))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        # Return as File Download
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rebalancing_plan.pdf"'
        return response