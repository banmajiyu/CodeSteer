import math

# Given expression: atan(sin(0.79288) / sqrt(26.081)) * 1.3725

# Step 1: compute sin(0.79288)
sin_val = math.sin(0.79288)

# Step 2: compute sqrt(26.081)
sqrt_val = math.sqrt(26.081)

# Step 3: divide
ratio = sin_val / sqrt_val

# Step 4: atan of ratio
atan_val = math.atan(ratio)

# Step 5: multiply by 1.3725
result = atan_val * 1.3725

print(f"sin(0.79288) = {sin_val:.15f}")
print(f"sqrt(26.081) = {sqrt_val:.15f}")
print(f"ratio = {ratio:.15f}")
print(f"atan(ratio) = {atan_val:.15f}")
print(f"result = {result:.15f}")
print(f"result (scientific) = {result:.12e}")