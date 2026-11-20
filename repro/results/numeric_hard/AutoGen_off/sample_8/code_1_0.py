import decimal

# Set high precision
decimal.getcontext().prec = 50

# Compute exp(0.7283) using Decimal's exp method
x = decimal.Decimal('0.7283')
result = x.exp()

print(result)