import math

# Step 1: arctan(15.555)
atan_val = math.atan(15.555)

# Step 2: cos(0.38337)
cos_val = math.cos(0.38337)

# Step 3: sum
sum_val = atan_val + cos_val

# Step 4: natural log
ln_val = math.log(sum_val)

# Step 5: multiply
result = ln_val * 1.8805

# Output
print(f"<<<{result:.15g}>>>")