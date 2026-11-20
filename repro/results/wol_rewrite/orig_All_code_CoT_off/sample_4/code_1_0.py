# Step-by-step truth values
tamika_lies = True
raymond_truth = not tamika_lies  # Raymond says Tamika tells truth, but she lies
willian_truth = raymond_truth    # Willian says Raymond tells truth
shaunda_truth = not willian_truth  # Shaunda says Willian lies
elanor_truth = shaunda_truth     # Elanor says Shaunda tells truth

print(elanor_truth)