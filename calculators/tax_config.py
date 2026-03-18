# calculators/tax_config.py
from decimal import Decimal

# --- UK Tax Thresholds (2024/25) ---
UK_TAX_CONFIG = {
    'ANNUAL_EXEMPT_AMOUNT': Decimal('3000.00'),
    'BASIC_RATE_THRESHOLD': Decimal('50270.00'),
    'BASIC_RATE_CGT': Decimal('0.10'),
    'HIGHER_RATE_CGT': Decimal('0.20'),
}

# --- US Tax Thresholds (Simplified 2024) ---
# Note: These are vast simplifications for demonstration.
# A professional app would require integration with a dedicated tax API or a much larger, regularly updated database table.

US_SHORT_TERM_BRACKETS = [
    {'up_to': Decimal('11600'), 'rate': Decimal('0.10')},
    {'up_to': Decimal('47150'), 'rate': Decimal('0.12')},
    {'up_to': Decimal('100525'), 'rate': Decimal('0.22')},
    {'up_to': Decimal('191950'), 'rate': Decimal('0.24')},
    {'up_to': Decimal('243725'), 'rate': Decimal('0.32')},
    {'up_to': Decimal('609350'), 'rate': Decimal('0.35')},
    {'up_to': Decimal('Infinity'), 'rate': Decimal('0.37')},
]

US_LONG_TERM_BRACKETS = {
    'single': [
        {'up_to': Decimal('47025'), 'rate': Decimal('0.00')},
        {'up_to': Decimal('518900'), 'rate': Decimal('0.15')},
        {'up_to': Decimal('Infinity'), 'rate': Decimal('0.20')},
    ],
    'married_jointly': [
        {'up_to': Decimal('94050'), 'rate': Decimal('0.00')},
        {'up_to': Decimal('583750'), 'rate': Decimal('0.15')},
        {'up_to': Decimal('Infinity'), 'rate': Decimal('0.20')},
    ]
}
