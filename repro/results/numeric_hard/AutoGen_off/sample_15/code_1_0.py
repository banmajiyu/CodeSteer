import math

# Compute each term
term1 = math.exp(0.3969)
term2 = math.tan(0.98101)
term3 = math.sqrt(127.638)

# Combine
result = term1 - term2 + term3

# Print with high precision
print(f"exp(0.3969) = {term1:.15g}")
print(f"tan(0.98101) = {term2:.15g}")
print(f"sqrt(127.638) = {term3:.15g}")
print(f"Result = {result:.15g}")