import math

# Compute the two parts
exp_part = math.exp(0.9926)
tan_part = math.tan(0.82085)

# Sum them
result = exp_part + tan_part

# Print with high precision
print(f"<<<{result:.15g}>>>")