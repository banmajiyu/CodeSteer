# Step-by-step logic
audrie_lies = True  # given
conception_truth = audrie_lies  # Conception says Audrie lies, which is true
teressa_truth = conception_truth  # Teressa says Conception tells truth
delfina_truth = not teressa_truth  # Delfina says Teressa lies
helene_truth = delfina_truth  # Helene says Delfina tells truth

print("Helene tells the truth:", helene_truth)
print("<<<" + ("Yes" if helene_truth else "No") + ">>>")