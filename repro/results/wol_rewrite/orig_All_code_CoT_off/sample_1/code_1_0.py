# Step-by-step truth evaluation
kristian_lies = True
sherrie_truth = kristian_lies  # Sherrie says Kristian lies (true statement)
delbert_truth = not sherrie_truth  # Delbert says Sherrie lies
jerry_truth = delbert_truth  # Jerry says Delbert tells the truth
shalonda_truth = jerry_truth  # Shalonda says Jerry tells the truth

print(shalonda_truth)