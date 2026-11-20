from decimal import Decimal, getcontext

# Set high precision
getcontext().prec = 50

x = Decimal('0.7283')
result = x.exp()

print(f"<<<{result}>>>")