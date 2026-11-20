from decimal import Decimal, getcontext

getcontext().prec = 50
value = Decimal('7671.664')
sqrt_value = value.sqrt()
print(sqrt_value)