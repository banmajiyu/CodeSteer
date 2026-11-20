# Step-by-step truth evaluation
raymond_truth = True
sal_truth = not raymond_truth  # Sal says Raymond lies
alexis_truth = not sal_truth   # Alexis says Sal lies
helene_truth = not alexis_truth  # Helene says Alexis lies
elanor_truth = not helene_truth  # Elanor says Helene lies

print(elanor_truth)