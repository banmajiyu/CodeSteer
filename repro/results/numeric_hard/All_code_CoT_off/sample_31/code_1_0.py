import math

# Step 1: ln(252.513)
inner_ln = math.log(252.513)

# Step 2: multiply by 1.8618
product = inner_ln * 1.8618

# Step 3: ln of the product
result = math.log(product)

# Step 4: output with high precision
print(f"<<<{result:.15e}>>>")