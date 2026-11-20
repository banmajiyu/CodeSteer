import math

# Step 1: compute atan(6.761)
inner_atan = math.atan(6.761)

# Step 2: compute cos(0.59531)
cos_val = math.cos(0.59531)

# Step 3: sum them
sum_val = inner_atan + cos_val

# Step 4: compute atan of the sum
result = math.atan(sum_val)

print(f"atan(6.761) = {inner_atan:.15f}")
print(f"cos(0.59531) = {cos_val:.15f}")
print(f"sum = {sum_val:.15f}")
print(f"final result = {result:.15f}")