# Step-by-step truth evaluation
amberly_lies = True
shenna_truth = not amberly_lies  # Shenna says Amberly tells truth
willian_truth = shenna_truth     # Willian says Shenna tells truth
raymond_truth = not willian_truth  # Raymond says Willian lies
sal_truth = not raymond_truth    # Sal says Raymond lies

print(sal_truth)