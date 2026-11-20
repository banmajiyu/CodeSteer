# Step-by-step truth evaluation
amberly_truth = True
jamey_truth = amberly_truth  # Jamey says Amberly tells the truth
shalonda_truth = not jamey_truth  # Shalonda says Jamey lies
antwan_truth = shalonda_truth  # Antwan says Shalonda tells the truth
alejandro_truth = not antwan_truth  # Alejandro says Antwan lies

print("Alejandro tells the truth:", alejandro_truth)
print("<<<Yes>>>" if alejandro_truth else "<<<No>>>")