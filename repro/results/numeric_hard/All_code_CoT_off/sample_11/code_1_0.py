from decimal import Decimal, getcontext

# Set high precision
getcontext().prec = 50

# Compute square root
value = Decimal('7671.664')
sqrt_value = value.sqrt()

# Print with at least 10 significant digits
print(f"<<<{sqrt_value}>>>")