import math

# Compute each term
term1 = math.sqrt(60.1996)
term2 = math.tan(0.29542)
term3 = math.sqrt(69.843)

# Combine
result = term1 - term2 + term3

# Print with high precision
print(f"sqrt(60.1996) = {term1:.15f}")
print(f"tan(0.29542) = {term2:.15f}")
print(f"sqrt(69.843) = {term3:.15f}")
print(f"Result = {result:.15f}")