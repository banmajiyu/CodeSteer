import math

# Step 1: compute sin(0.63286)
inner_sin = math.sin(0.63286)

# Step 2: compute sqrt(30.238)
sqrt_val = math.sqrt(30.238)

# Step 3: divide
quotient = inner_sin / sqrt_val

# Step 4: outer sine
result = math.sin(quotient)

# Step 5: output with high precision
print(f"<<<{result:.15g}>>>")