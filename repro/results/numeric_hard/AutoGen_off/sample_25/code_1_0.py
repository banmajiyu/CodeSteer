import math

# Given expression: sqrt(sin(0.40039) / sqrt(5.163))

# Step 1: compute sin(0.40039) in radians
sin_val = math.sin(0.40039)

# Step 2: compute sqrt(5.163)
sqrt_5163 = math.sqrt(5.163)

# Step 3: divide
div_val = sin_val / sqrt_5163

# Step 4: take sqrt of result
result = math.sqrt(div_val)

print(f"sin(0.40039) = {sin_val:.15f}")
print(f"sqrt(5.163) = {sqrt_5163:.15f}")
print(f"division = {div_val:.15f}")
print(f"final result = {result:.15f}")
print(f"final result (scientific) = {result:.12e}")