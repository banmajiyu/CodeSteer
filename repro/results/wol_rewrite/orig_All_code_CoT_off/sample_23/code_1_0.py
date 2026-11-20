# Step-by-step truth evaluation
leda_truth = True  # given
alexis_truth = not leda_truth  # Alexis says Leda lies
sal_truth = not alexis_truth  # Sal says Alexis lies
phoebe_truth = sal_truth      # Phoebe says Sal tells truth
gwenn_truth = phoebe_truth    # Gwenn says Phoebe tells truth

print(gwenn_truth)
print("<<<Yes>>>" if gwenn_truth else "<<<No>>>")