from decimal import Decimal, getcontext

getcontext().prec = 50
x = Decimal('0.7283')
result = x.exp()
print(f"<<<{result}>>>")