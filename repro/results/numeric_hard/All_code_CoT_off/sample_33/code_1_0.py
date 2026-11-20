import math

# Step 1: arctan(6.761)
a = math.atan(6.761)

# Step 2: cos(0.59531)
b = math.cos(0.59531)

# Step 3: sum
s = a + b

# Step 4: final arctan
result = math.atan(s)

# Output with high precision
print(f"<<<{result:.15g}>>>")