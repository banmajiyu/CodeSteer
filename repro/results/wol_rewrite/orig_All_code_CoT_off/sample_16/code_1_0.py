# Step-by-step truth evaluation
ka_lies = True
christie_truth = not ka_lies  # Christie says Ka tells truth
jerry_truth = not christie_truth  # Jerry says Christie lies
crista_truth = not jerry_truth  # Crista says Jerry lies
yoland_truth = crista_truth  # Yoland says Crista tells truth

print("Yes" if yoland_truth else "No")