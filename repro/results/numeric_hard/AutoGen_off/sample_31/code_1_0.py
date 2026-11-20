import math

# Step 1: compute ln(252.513)
inner_ln = math.log(252.513)

# Step 2: multiply by 1.8618
product = inner_ln * 1.8618

# Step 3: take ln of the product
result = math.log(product)

print(inner_ln)
print(product)
print(result)