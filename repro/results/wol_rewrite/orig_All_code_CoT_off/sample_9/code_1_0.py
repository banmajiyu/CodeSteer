# Step by step truth values
rashida_truth = True
jim_truth = not rashida_truth  # Jim says Rashida lies
alejandro_truth = not jim_truth  # Alejandro says Jim lies
tamika_truth = alejandro_truth  # Tamika says Alejandro tells truth
fidel_truth = not tamika_truth  # Fidel says Tamika lies

print("Fidel tells the truth:", fidel_truth)
print("<<<" + ("Yes" if fidel_truth else "No") + ">>>")