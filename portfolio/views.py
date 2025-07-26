# portfolio/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DeleteView
from .models import StockHolding, HistoricalPrice
from .forms import StockHoldingForm
import requests
import os
from decimal import Decimal, InvalidOperation
import json

# Retrieve API Key from settings (which gets it from .env)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

def get_stock_quote(symbol):
    if not ALPHA_VANTAGE_API_KEY:
        print("Alpha Vantage API key not found in environment variables.")
        return None

    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if "Error Message" in data:
            print(f"Alpha Vantage API Error for {symbol}: {data['Error Message']}")
            return None
        if "Note" in data:
             print(f"Alpha Vantage API Note for {symbol}: {data['Note']}")

        if "Time Series (Daily)" in data and data["Time Series (Daily)"]:
            latest_date = max(data["Time Series (Daily)"].keys())
            current_price_str = data["Time Series (Daily)"][latest_date]["4. close"]
            try:
                current_price = Decimal(current_price_str)
                return current_price
            except InvalidOperation:
                print(f"Error converting price string '{current_price_str}' to Decimal for {symbol}.")
                return None
        else:
            print(f"No stock data found for {symbol} (Alpha Vantage response: {data})")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None
    except KeyError as e:
        print(f"Unexpected data structure for {symbol}: {e}. Response: {data}")
        return None

@login_required
def portfolio_list(request):
    user_holdings = StockHolding.objects.filter(user=request.user).order_by('stock_symbol')

    enhanced_holdings = []
    total_portfolio_value = Decimal('0.00') # Initialize Decimal
    total_investment = Decimal('0.00')    # Initialize Decimal
    total_profit_loss = Decimal('0.00')   # Initialize Decimal

    for holding in user_holdings:
        current_price = get_stock_quote(holding.stock_symbol)
        total_value = None
        profit_loss = None

        if current_price is not None:
            total_value = current_price * holding.quantity
            profit_loss = (current_price - holding.purchase_price) * holding.quantity

            total_portfolio_value += total_value # Add to overall total
            total_investment += holding.purchase_price * holding.quantity # Add to overall investment
            if profit_loss is not None:
                total_profit_loss += profit_loss # Add to overall P/L

        enhanced_holdings.append({
            'holding': holding,
            'current_price': current_price,
            'total_value': total_value,
            'profit_loss': profit_loss,
        })

    if request.method == 'POST':
        form = StockHoldingForm(request.POST)
        if form.is_valid():
            stock_holding = form.save(commit=False)
            stock_holding.user = request.user
            stock_holding.save()
            return redirect('portfolio:portfolio_list')
    else:
        form = StockHoldingForm()

    context = {
        'form': form,
        'holdings': enhanced_holdings,
        'total_portfolio_value': total_portfolio_value, # <--- NEW CONTEXT VARIABLE
        'total_investment': total_investment,           # <--- NEW CONTEXT VARIABLE
        'total_profit_loss': total_profit_loss,         # <--- NEW CONTEXT VARIABLE
    }
    return render(request, 'portfolio/portfolio_list.html', context)

# --- UPDATED VIEW FOR STOCK CHART (FOR CHART.JS) ---
def stock_chart_view(request, symbol): # Function now correctly accepts 'symbol'
    # 1. Fetch historical data for the given stock symbol, ordered by date
    historical_data = HistoricalPrice.objects.filter(
        stock_symbol=symbol # <--- CHANGE THIS: Use 'symbol' here
    ).order_by('date')

    # 2. Extract dates and prices, converting to suitable Python types
    #    Dates should be strings in 'YYYY-MM-DD' format for JavaScript
    #    Prices should be floats for Chart.js
    dates = [data.date.strftime('%Y-%m-%d') for data in historical_data]
    prices = [float(data.close_price) for data in historical_data]

    # 3. Convert lists to JSON strings
    #    json.dumps() serializes the list into a JSON string
    #    This string will then be parsed by JavaScript in the template
    dates_json = json.dumps(dates)
    prices_json = json.dumps(prices)

    context = {
        'stock_symbol': symbol, # <--- CHANGE THIS: Use 'symbol' here for the template context
        'dates_json': dates_json,
        'prices_json': prices_json,
    }
    return render(request, 'portfolio/stock_chart.html', context)

# Class-based views (StockHoldingUpdateView, StockHoldingDeleteView) remain unchanged
class StockHoldingUpdateView(UpdateView):
    model = StockHolding
    form_class = StockHoldingForm
    template_name = 'portfolio/stockholding_form.html'
    success_url = reverse_lazy('portfolio:portfolio_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        if form.instance.user != self.request.user:
            return self.handle_no_permission()
        return super().form_valid(form)

class StockHoldingDeleteView(DeleteView):
    model = StockHolding
    template_name = 'portfolio/stockholding_confirm_delete.html'
    success_url = reverse_lazy('portfolio:portfolio_list')

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        if self.get_object().user != self.request.user:
            return self.handle_no_permission()
        return super().form_valid(form)