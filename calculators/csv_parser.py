# calculators/csv_parser.py
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

class CSVImportError(Exception):
    pass

def parse_brokerage_csv(file_stream) -> dict:
    """
    Parses a CSV file containing trading history and normalizes it into
    a list of purchase lots and a potential sale event, intended for consumption
    by the Capital Gains clarity API.
    
    Accepts an in-memory file stream (from request.FILES).

    Expected standard CSV Headers (loose fuzzy matching):
    Date, Action/Type (Buy/Sell), Symbol, Quantity, Price, Fees/Commission

    Returns a dict:
    {
        'symbol': 'AAPL',
        'purchase_lots': [{'date': 'YYYY-MM-DD', 'quantity': 10, 'price': 150.0, 'fees': 0}],
        'potential_sales': [{'date': 'YYYY-MM-DD', 'quantity': 5, 'price': 160.0, 'fees': 0}]
    }
    """
    try:
        # Decode stream if it's binary
        if isinstance(file_stream.read(0), bytes):
            decoded_file = file_stream.read().decode('utf-8-sig')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
        else:
            csv_reader = csv.DictReader(file_stream)
    except Exception as e:
        raise CSVImportError(f"Failed to read file: {str(e)}")

    headers = csv_reader.fieldnames
    if not headers:
         raise CSVImportError("The CSV file appears to be empty or lacks headers.")

    # Lowercase and strip headers for fuzzy matching
    normalized_headers = {h.lower().strip(): h for h in headers if h}
    
    # Identify key columns based on common names
    def find_column(options):
        for opt in options:
            if opt in normalized_headers:
                return normalized_headers[opt]
        return None

    date_col = find_column(['date', 'time', 'execution date', 'trade date'])
    action_col = find_column(['action', 'type', 'transaction type', 'side'])
    symbol_col = find_column(['symbol', 'ticker', 'asset'])
    qty_col = find_column(['quantity', 'qty', 'amount', 'shares'])
    price_col = find_column(['price', 'execution price', 'avg price'])
    fees_col = find_column(['fees', 'commission', 'fee', 'commissions'])

    if not all([date_col, action_col, symbol_col, qty_col, price_col]):
        missing = []
        if not date_col: missing.append('Date')
        if not action_col: missing.append('Action (Buy/Sell)')
        if not symbol_col: missing.append('Symbol')
        if not qty_col: missing.append('Quantity')
        if not price_col: missing.append('Price')
        raise CSVImportError(f"Could not identify required columns. Missing: {', '.join(missing)}")

    purchase_lots = []
    potential_sales = []
    detected_symbol = None

    for row_num, row in enumerate(csv_reader, start=2):
        if not row.get(symbol_col):
             continue # Skip empty rows

        symbol_val = row[symbol_col].strip().upper()
        
        if detected_symbol is None:
             detected_symbol = symbol_val
        elif symbol_val != detected_symbol:
             # For v1, we assume the user uploads a CSV filtered for ONE stock.
             # If multiple are found, we just filter for the first one found to keep it simple.
             continue

        action_val = row[action_col].strip().lower()
        is_buy = 'buy' in action_val
        is_sell = 'sell' in action_val

        if not (is_buy or is_sell):
            continue # Skip dividends, deposits, etc.

        try:
             # Handle various date formats by standardising to YYYY-MM-DD
             raw_date = row[date_col].strip()
             # Split by T for ISO format, space for standard time, etc.
             date_part = raw_date.split('T')[0].split(' ')[0]
             
             try:
                 parsed_date = datetime.strptime(date_part, '%Y-%m-%d').date()
             except ValueError:
                 try:
                     parsed_date = datetime.strptime(date_part, '%m/%d/%Y').date()
                 except ValueError:
                     parsed_date = datetime.strptime(date_part, '%d/%m/%Y').date()
                     
             date_str = parsed_date.strftime('%Y-%m-%d')
             
             # Handle numbers that might have commas or negative signs
             qty_str = row[qty_col].replace(',', '').replace('-', '').strip()
             price_str = row[price_col].replace(',', '').replace('$', '').strip()
             
             qty = Decimal(qty_str)
             price = Decimal(price_str)
             
             fee_val = Decimal('0.00')
             if fees_col and row.get(fees_col):
                  fee_str = row[fees_col].replace(',', '').replace('$', '').replace('-', '').strip()
                  if fee_str:
                       fee_val = Decimal(fee_str)

             record = {
                 'date': date_str,
                 'quantity': qty,
                 'price': price,
                 'fees': fee_val
             }

             if is_buy:
                 purchase_lots.append(record)
             elif is_sell:
                 potential_sales.append(record)

        except (ValueError, InvalidOperation) as e:
            continue # Skip rows that fail numeric/date parsing

    # Sort lots by date
    purchase_lots.sort(key=lambda x: x['date'])
    potential_sales.sort(key=lambda x: x['date'])

    return {
        'symbol': detected_symbol or 'Unknown Asset',
        'purchase_lots': [{'date': r['date'], 'quantity': f"{r['quantity']:.4f}", 'price': f"{r['price']:.4f}", 'fees': f"{r['fees']:.4f}"} for r in purchase_lots],
        'potential_sales': [{'date': r['date'], 'quantity': f"{r['quantity']:.4f}", 'price': f"{r['price']:.4f}", 'fees': f"{r['fees']:.4f}"} for r in potential_sales]
    }
