import math

# Step 1: atan(12.157)
a = math.atan(12.157)

# Step 2: cos(0.49945)
b = math.cos(0.49945)

# Step 3: sum
s = a + b

# Step 4: sine of sum
val = math.sin(s)

# Step 5: multiply by 2.429
result = val * 2.429

# Output with high precision
print(f"<<<{result:.15e}>>>")