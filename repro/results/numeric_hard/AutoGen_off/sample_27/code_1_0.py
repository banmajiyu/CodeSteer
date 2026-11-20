import math

# Compute the expression
sqrt_val = math.sqrt(499.966)
exp_val = math.exp(-0.9854)
result = math.sin(sqrt_val + exp_val)

print(f"sqrt(499.966) = {sqrt_val:.15f}")
print(f"exp(-0.9854) = {exp_val:.15f}")
print(f"sum = {sqrt_val + exp_val:.15f}")
print(f"sin(sum) = {result:.15e}")