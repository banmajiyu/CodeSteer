# Step-by-step truth evaluation
fletcher_truth = True
conception_truth = fletcher_truth  # Conception says Fletcher tells truth
bernita_truth = conception_truth   # Bernita says Conception tells truth
jamey_truth = bernita_truth        # Jamey says Bernita tells truth
teressa_truth = not jamey_truth    # Teressa says Jamey lies

print(teressa_truth)