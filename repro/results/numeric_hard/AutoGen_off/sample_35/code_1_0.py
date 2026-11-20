import math

# Given expression: sin(sin(0.63286) / sqrt(30.238))

inner_sin = math.sin(0.63286)
sqrt_val = math.sqrt(30.238)
division = inner_sin / sqrt_val
result = math.sin(division)

print("sin(0.63286) =", inner_sin)
print("sqrt(30.238) =", sqrt_val)
print("division =", division)
print("result =", result)
print("result (scientific) =", f"{result:.15e}")