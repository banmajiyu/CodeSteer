import math

# Step-by-step computation
exp_val = math.exp(0.3969)
tan_val = math.tan(0.98101)
sqrt_val = math.sqrt(127.638)

result = exp_val - tan_val + sqrt_val

# Print intermediate values for verification
print("exp(0.3969) =", exp_val)
print("tan(0.98101) =", tan_val)
print("sqrt(127.638) =", sqrt_val)
print("Result =", result)
print(f"<<<{result:.15g}>>>")