import math

log_val = math.log10(25.9396)
sin_val = math.sin(0.27417)
sqrt_val = math.sqrt(7.412)

result = log_val - sin_val + sqrt_val

print(f"log10(25.9396) = {log_val:.15f}")
print(f"sin(0.27417) = {sin_val:.15f}")
print(f"sqrt(7.412) = {sqrt_val:.15f}")
print(f"Result = {result:.15f}")
print(f"<<<{result:.15g}>>>")