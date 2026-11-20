import math

# Step 1: sqrt(499.966)
sqrt_part = math.sqrt(499.966)

# Step 2: exp(-0.9854)
exp_part = math.exp(-0.9854)

# Step 3: sum
total = sqrt_part + exp_part

# Step 4: sine
result = math.sin(total)

# Step 5: output
print(f"<<<{result:.15e}>>>")