import mpmath as mp

# Set high precision
mp.mp.dps = 50

# Compute asin(0.18035)
result = mp.asin(mp.mpf('0.18035'))

# Print with high precision
print(result)