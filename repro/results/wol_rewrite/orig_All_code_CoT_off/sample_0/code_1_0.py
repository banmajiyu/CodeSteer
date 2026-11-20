# Step-by-step truth evaluation
sherrie_truth = True
vernell_truth = sherrie_truth  # Vernell says Sherrie tells truth
alexis_truth = not vernell_truth  # Alexis says Vernell lies
michaela_truth = alexis_truth  # Michaela says Alexis tells truth
elanor_truth = michaela_truth  # Elanor says Michaela tells truth

print("Sherrie:", sherrie_truth)
print("Vernell:", vernell_truth)
print("Alexis:", alexis_truth)
print("Michaela:", michaela_truth)
print("Elanor:", elanor_truth)

print("<<<" + ("Yes" if elanor_truth else "No") + ">>>")