# Step-by-step truth evaluation
ryan_lies = True  # given
kristian_truth = ryan_lies  # Kristian says Ryan lies (true)
teressa_truth = kristian_truth  # Teressa says Kristian tells truth
amberly_truth = teressa_truth  # Amberly says Teressa tells truth
jamey_truth = amberly_truth  # Jamey says Amberly tells truth

print("Yes" if jamey_truth else "No")