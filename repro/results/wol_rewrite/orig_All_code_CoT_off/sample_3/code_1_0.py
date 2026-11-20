# Step-by-step truth evaluation
christie_truth = True
ka_truth = christie_truth  # Ka says Christie tells the truth
delbert_truth = not ka_truth  # Delbert says Ka lies
leda_truth = delbert_truth  # Leda says Delbert tells the truth
lorine_truth = leda_truth  # Lorine says Leda tells the truth

print(lorine_truth)
print("<<<Yes>>>" if lorine_truth else "<<<No>>>")