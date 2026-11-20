import math

# Step 1: arctan(14.931)
a = math.atan(14.931)

# Step 2: cos(0.88582)
b = math.cos(0.88582)

# Step 3: sum
s = a + b

# Step 4: arctan of sum
c = math.atan(s)

# Step 5: multiply by 1.3046
result = c * 1.3046

# Output with high precision
print(f"<<<{result:.15g}>>>")