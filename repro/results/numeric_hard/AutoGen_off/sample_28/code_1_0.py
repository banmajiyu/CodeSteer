import math

# Given expression: ln(atan(15.555) + cos(0.38337)) * 1.8805

atan_val = math.atan(15.555)         # arctangent in radians
cos_val = math.cos(0.38337)          # cosine in radians
inner_sum = atan_val + cos_val
ln_val = math.log(inner_sum)         # natural logarithm
result = ln_val * 1.8805

print(f"atan(15.555) = {atan_val}")
print(f"cos(0.38337) = {cos_val}")
print(f"sum = {inner_sum}")
print(f"ln(sum) = {ln_val}")
print(f"result = {result:.15g}")