from decimal import Decimal, ROUND_UP, getcontext

getcontext().prec = 10

def quantize_up(value, precision='1.'):
    return value.quantize(Decimal(precision), rounding=ROUND_UP)

def calculate_purchase_amount(krw, price, precision='0.000001'):
    return (krw / price).quantize(Decimal(precision), rounding=ROUND_UP)
