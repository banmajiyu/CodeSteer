import math

# Step 1: sqrt(60.1996)
term1 = math.sqrt(60.1996)

# Step 2: tan(0.29542) in radians
term2 = math.tan(0.29542)

# Step 3: sqrt(69.843)
term3 = math.sqrt(69.843)

# Step 4: Combine
result = term1 - term2 + term3

# Step 5: Output with high precision
print(f"<<<{result:.15g}>>>")