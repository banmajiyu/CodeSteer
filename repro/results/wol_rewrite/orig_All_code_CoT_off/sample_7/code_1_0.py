# Step-by-step truth evaluation
jim_lies = True  # given

# Crista says Jim lies
crista_truth = jim_lies  # True

# Vernell says Crista tells the truth
vernell_truth = crista_truth  # True

# Bernita says Vernell tells the truth
bernita_truth = vernell_truth  # True

# Millicent says Bernita tells the truth
millicent_truth = bernita_truth  # True

print("Millicent tells the truth:", millicent_truth)
print("<<<Yes>>>" if millicent_truth else "<<<No>>>")