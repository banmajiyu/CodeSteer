import math

# Step 1: sin(0.40039)
sin_val = math.sin(0.40039)

# Step 2: sqrt(5.163)
sqrt_5163 = math.sqrt(5.163)

# Step 3: division
division_result = sin_val / sqrt_5163

# Step 4: outer square root
final_result = math.sqrt(division_result)

print(f"{final_result:.15g}")
print(f"<<<{final_result:.15g}>>>")