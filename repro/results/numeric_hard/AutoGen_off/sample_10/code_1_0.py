import decimal

# Set high precision
decimal.getcontext().prec = 50

# Compute log10(421.381) using natural log and change of base
x = decimal.Decimal('421.381')
ln_x = x.ln()
ln_10 = decimal.Decimal(10).ln()
log10_x = ln_x / ln_10

print(log10_x)