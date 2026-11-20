# Step-by-step truth evaluation
vernell_truth = True
kandi_truth = vernell_truth  # Kandi says Vernell tells truth
alexis_truth = kandi_truth    # Alexis says Kandi tells truth
sima_truth = not alexis_truth # Sima says Alexis lies
phoebe_truth = sima_truth     # Phoebe says Sima tells truth

print(phoebe_truth)