import mpmath as mp

# Set high precision
mp.mp.dps = 50

# Compute cos(0.33907)
result = mp.cos(mp.mpf('0.33907'))

# Print with high precision
print(result)