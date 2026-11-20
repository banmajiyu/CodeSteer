import math

# Given expression: sin(ln(202.979) * 0.5768) * 1.6101

# Step 1: natural log of 202.979
ln_val = math.log(202.979)

# Step 2: multiply by 0.5768
arg = ln_val * 0.5768

# Step 3: sine of that (in radians)
sin_val = math.sin(arg)

# Step 4: multiply by 1.6101
result = sin_val * 1.6101

print(f"ln(202.979) = {ln_val}")
print(f"arg = {arg}")
print(f"sin(arg) = {sin_val}")
print(f"result = {result:.15g}")