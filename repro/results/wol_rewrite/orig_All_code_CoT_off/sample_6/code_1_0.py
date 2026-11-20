# Step-by-step evaluation
shalonda_lies = True
teressa_truth = not shalonda_lies  # Teressa says Shalonda tells truth
teressa_lies = not teressa_truth
tamika_truth = teressa_lies  # Tamika says Teressa lies
lorine_truth = tamika_truth  # Lorine says Tamika tells truth
jaymie_truth = not lorine_truth  # Jaymie says Lorine lies

print("Jaymie tells the truth:", jaymie_truth)
print("<<<" + ("Yes" if jaymie_truth else "No") + ">>>")