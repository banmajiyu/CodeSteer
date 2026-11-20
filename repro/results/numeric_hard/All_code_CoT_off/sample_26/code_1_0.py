import math

# Step 1: compute sin(0.79288)
sin_val = math.sin(0.79288)

# Step 2: compute sqrt(26.081)
sqrt_val = math.sqrt(26.081)

# Step 3: divide
ratio = sin_val / sqrt_val

# Step 4: arctangent
atan_val = math.atan(ratio)

# Step 5: multiply by 1.3725
result = atan_val * 1.3725

# Output with high precision
print(f"<<<{result:.15g}>>>")