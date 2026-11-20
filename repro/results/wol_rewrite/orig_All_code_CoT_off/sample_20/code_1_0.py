# Step-by-step truth values
sima_lies = True
millie_truth = not sima_lies  # Millie says Sima tells truth, but Sima lies
jerry_truth = millie_truth    # Jerry says Millie tells truth
vina_truth = not jerry_truth  # Vina says Jerry lies
maybelle_truth = vina_truth   # Maybelle says Vina tells truth

print(maybelle_truth)