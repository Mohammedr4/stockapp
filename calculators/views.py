# calculators/views.py
import io
import os
import requests
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
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
    DRIPRequestSerializer,
    CSVUploadSerializer,
    SavedRepriceStrategySerializer,
    SavedCapitalGainsScenarioSerializer
)

# Model Imports
# This was the missing piece causing the NameError
from .models import (
    SavedRepriceStrategy,
    SavedCapitalGainsScenario,
    CGSPurchaseLot,
    CGSSaleDetails,
    CGSTaxProfile,
    CGSResult,
    SavedDRIPProjection,
)

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

@login_required
def calculators_index(request):
    """ Redirects old calculators index to the home workspace page. """
    return redirect('home')

def drip_dashboard_view(request):
    """ Renders the template for the new DRIP Predictor. """
    return render(request, 'calculators/drip_dashboard.html')

def clarity_dashboard_view(request):
    """ Renders the template for the new Capital Gains Clarity Dashboard. """
    return render(request, 'calculators/clarity_dashboard.html')

def reprice_dashboard_view(request):
    """ Renders the template for the new Repricing Strategy Dashboard. """
    return render(request, 'calculators/reprice_dashboard.html')



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

class CSVImportAPIView(APIView):
    """ API endpoint for uploading and parsing brokerage CSV files. """
    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        csv_file = serializer.validated_data['file']
        
        # Validations
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV.'}, status=status.HTTP_400_BAD_REQUEST)
        if csv_file.size > 2 * 1024 * 1024: # 2MB Limit
            return Response({'error': 'File too large. Limit is 2MB.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .csv_parser import parse_brokerage_csv, CSVImportError
            parsed_data = parse_brokerage_csv(csv_file)
            return Response(parsed_data, status=status.HTTP_200_OK)
        except CSVImportError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'An unexpected error occurred while processing the file.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RepriceAPIView(APIView):
    """ The API endpoint for the Repricing Strategy Dashboard. """
    def post(self, request, *args, **kwargs):
        serializer = RepriceRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Standard DRF error response is preferred over brittle dictionary traversal
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        position = data['position']
        strategy = data['strategy']
        
        try:
            if strategy['mode'] == 'shares':
                from .reprice_engine import calculate_reprice_by_shares
                results = calculate_reprice_by_shares(position, strategy['value'])
            elif strategy['mode'] == 'price':
                from .reprice_engine import calculate_reprice_by_target
                results = calculate_reprice_by_target(position, strategy['value'])
            elif strategy['mode'] == 'tranches':
                from .reprice_engine import calculate_trade_scenario
                if 'tranches' not in strategy or not strategy['tranches']:
                    return Response({'error': 'Tranches data is required for this mode.'}, status=status.HTTP_400_BAD_REQUEST)
                results = calculate_trade_scenario(position, strategy['tranches'])
            else:
                return Response({'error': 'Invalid strategy mode.'}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(results, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DRIPAPIView(APIView):
    """ The API endpoint for the DRIP Predictor Dashboard. """
    def post(self, request, *args, **kwargs):
        serializer = DRIPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        
        try:
            from .drip_engine import calculate_drip_projection
            response_data = calculate_drip_projection(
                initial_principal=data['initial_principal'],
                annual_contribution=data['annual_contribution'],
                dividend_yield_percent=data['dividend_yield_percent'],
                annual_appreciation_percent=data['annual_appreciation_percent'],
                years_to_grow=data['years_to_grow']
            )
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        mode = data.get('strategy_mode', 'shares')

        if mode == 'tranches':
            strategy_name = "Scale-In Simulator"
            tranches = data.get('tranches', [])
            strategy_desc = f"{len(tranches)} limit order(s)"
            results = {
                'Final Average Price': f"${data.get('final_average_price', 'N/A')}",
                'Total Incremental Investment': f"${data.get('total_additional_investment', 'N/A')}",
                'New Total Shares': data.get('total_shares', 'N/A'),
                'Lowest Price Reached': f"${data.get('lowest_price_reached', 'N/A')}",
                'Breakeven Recovery (After)': f"{data.get('breakeven_recovery_percent', 'N/A')}%",
                'Breakeven Recovery (Before)': f"{data.get('original_recovery_percent', 'N/A')}%",
            }
            scenario_steps = data.get('scenario_steps', [])
        elif mode == 'shares':
            strategy_name = "Buy Shares"
            strategy_desc = f"Buy {data.get('strategy_value', 'N/A')} additional shares"
            results = {
                'New Average Price': f"${data.get('new_average_price', 'N/A')}",
                'New Total Shares': data.get('total_shares', 'N/A'),
                'Additional Investment': f"${data.get('additional_investment', 'N/A')}",
            }
            scenario_steps = []
        else:  # price / target average
            strategy_name = "Target Average"
            strategy_desc = f"Target average price: ${data.get('strategy_value', 'N/A')}"
            results = {
                'Shares Needed': data.get('additional_shares_needed', 'N/A'),
                'New Total Shares': data.get('total_shares', 'N/A'),
                'Additional Investment': f"${data.get('additional_investment', 'N/A')}",
            }
            scenario_steps = []

        context = {
            'data': {
                'current_shares': data.get('current_shares'),
                'average_price': data.get('average_price'),
                'market_price': data.get('market_price'),
                'strategy_name': strategy_name,
                'strategy_desc': strategy_desc,
            },
            'results': results,
            'scenario_steps': scenario_steps,
        }

        pdf = render_to_pdf('calculators/pdf_report.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="StockSavvy_Report.pdf"'
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

        try:
            name = request.data.get('name', '')
            if not name:
                return Response({'error': 'Scenario name is required.'}, status=status.HTTP_400_BAD_REQUEST)

            input_data = request.data.get('input_data', {})
            result_data = request.data.get('result_data', {})

            asset_name = input_data.get('asset_name', 'Asset')

            scenario = SavedCapitalGainsScenario.objects.create(
                user=request.user,
                name=name,
                asset_name=asset_name
            )

            # Save purchase lots
            for lot in input_data.get('purchase_lots', []):
                CGSPurchaseLot.objects.create(
                    scenario=scenario,
                    date=lot.get('date'),
                    quantity=lot.get('quantity', 0),
                    price=lot.get('price', 0),
                    fees=lot.get('fees', 0)
                )

            # Save sale details
            sale = input_data.get('sale', {})
            if sale:
                CGSSaleDetails.objects.create(
                    scenario=scenario,
                    date=sale.get('date'),
                    quantity=sale.get('quantity', 0),
                    price=sale.get('price', 0),
                    fees=sale.get('fees', 0)
                )

            # Save tax profile
            tax_profile = input_data.get('tax_profile', {})
            if tax_profile:
                CGSTaxProfile.objects.create(
                    scenario=scenario,
                    jurisdiction=tax_profile.get('jurisdiction', 'US'),
                    annual_income=tax_profile.get('annual_income', 0),
                    filing_status=tax_profile.get('filing_status', 'single')
                )

            # Save results
            results = result_data.get('results', {})
            summary = result_data.get('summary', {})
            if results:
                CGSResult.objects.create(
                    scenario=scenario,
                    gross_gain_loss=results.get('gross_gain_loss', 0),
                    total_sale_proceeds=results.get('total_sale_proceeds', 0),
                    total_purchase_cost=results.get('total_purchase_cost', 0),
                    estimated_tax=results.get('estimated_tax', 0),
                    net_gain_loss=results.get('net_gain_loss', 0),
                    holding_period=summary.get('holding_period', ''),
                    gain_loss_type=summary.get('gain_loss_type', '')
                )

            serializer = SavedCapitalGainsScenarioSerializer(scenario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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


class SavedDRIPProjectionAPIView(APIView):
    """List, save, and delete DRIP projections."""

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        projections = SavedDRIPProjection.objects.filter(user=request.user)
        data = [{
            'id': p.id,
            'name': p.name,
            'created_at': p.created_at,
            'initial_principal': str(p.initial_principal),
            'annual_contribution': str(p.annual_contribution),
            'dividend_yield_percent': str(p.dividend_yield_percent),
            'annual_appreciation_percent': str(p.annual_appreciation_percent),
            'years_to_grow': p.years_to_grow,
            'final_balance': str(p.final_balance),
            'total_dividends': str(p.total_dividends),
        } for p in projections]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            d = request.data
            proj = SavedDRIPProjection.objects.create(
                user=request.user,
                name=d.get('name', 'My Projection'),
                initial_principal=d.get('initial_principal', 0),
                annual_contribution=d.get('annual_contribution', 0),
                dividend_yield_percent=d.get('dividend_yield_percent', 0),
                annual_appreciation_percent=d.get('annual_appreciation_percent', 0),
                years_to_grow=d.get('years_to_grow', 10),
                final_balance=d.get('final_balance', 0),
                total_dividends=d.get('total_dividends', 0),
            )
            return Response({'id': proj.id, 'name': proj.name}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            proj = SavedDRIPProjection.objects.get(pk=pk, user=request.user)
            proj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except SavedDRIPProjection.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
