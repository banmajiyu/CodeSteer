from decimal import Decimal, getcontext

getcontext().prec = 50  # high precision

value = Decimal('2648.586')
result = value.sqrt()

print(f"<<<{result}>>>")