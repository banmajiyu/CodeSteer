import math

ln_val = math.log(9.314)
tan_val = math.tan(0.24816)
sqrt_val = math.sqrt(139.681)

result = ln_val - tan_val + sqrt_val

print(f"{ln_val:.15f}")
print(f"{tan_val:.15f}")
print(f"{sqrt_val:.15f}")
print(f"<<<{result:.15g}>>>")