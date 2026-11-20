import math

# Step 1: compute atan(14.931)
a = math.atan(14.931)

# Step 2: compute cos(0.88582)
b = math.cos(0.88582)

# Step 3: sum them
s = a + b

# Step 4: compute atan of the sum
c = math.atan(s)

# Step 5: multiply by 1.3046
result = c * 1.3046

print(f"{result:.15g}")