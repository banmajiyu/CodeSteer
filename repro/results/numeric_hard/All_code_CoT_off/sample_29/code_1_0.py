import math

# Step 1: arctan(22.855)
atan_val = math.atan(22.855)

# Step 2: cos(0.84886)
cos_val = math.cos(0.84886)

# Step 3: sum
sum_val = atan_val + cos_val

# Step 4: natural log
result = math.log(sum_val)

# Step 5: output with high precision
print(f"<<<{result:.15g}>>>")