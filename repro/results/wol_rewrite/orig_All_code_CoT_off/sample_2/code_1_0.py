# Step-by-step truth evaluation
vina_truth = True
helene_truth = not vina_truth  # Helene says Vina lies
kandi_truth = helene_truth     # Kandi says Helene tells truth
jamey_truth = not kandi_truth  # Jamey says Kandi lies
ka_truth = not jamey_truth     # Ka says Jamey lies

print(ka_truth)