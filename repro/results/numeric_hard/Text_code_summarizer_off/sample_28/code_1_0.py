import math

atan_val = math.atan(15.555)
cos_val = math.cos(0.38337)
sum_val = atan_val + cos_val
ln_val = math.log(sum_val)
result = ln_val * 1.8805

print(f"<<<{result:.15g}>>>")