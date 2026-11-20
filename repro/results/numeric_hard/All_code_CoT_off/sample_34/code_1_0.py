import math

# Step 1: natural log
ln_val = math.log(99.831)

# Step 2: multiply by 0.5433
angle = ln_val * 0.5433

# Step 3: sine of angle (radians)
sin_val = math.sin(angle)

# Step 4: multiply by 1.9325
result = sin_val * 1.9325

# Step 5: output with high precision
print(f"<<<{result:.15g}>>>")