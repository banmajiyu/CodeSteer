import math

# Step 1: compute atan(12.157)
a = math.atan(12.157)

# Step 2: compute cos(0.49945)
b = math.cos(0.49945)

# Step 3: sum them
s = a + b

# Step 4: compute sin of the sum
sin_val = math.sin(s)

# Step 5: multiply by 2.429
result = sin_val * 2.429

print(f"{result:.15g}")