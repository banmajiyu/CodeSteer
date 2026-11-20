import math

ln_val = math.log(99.831)
angle = ln_val * 0.5433
sin_val = math.sin(angle)
result = sin_val * 1.9325

print(f"<<<{result:.15g}>>>")