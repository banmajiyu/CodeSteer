import mpmath as mp

# Set high precision
mp.mp.dps = 50

# Compute sin(0.41293) in radians
result = mp.sin(mp.mpf('0.41293'))

print(result)