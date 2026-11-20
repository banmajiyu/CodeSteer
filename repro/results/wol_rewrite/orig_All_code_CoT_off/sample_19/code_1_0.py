# Truth chain evaluation
ryan_truth = True  # given
sal_truth = ryan_truth  # Sal says Ryan tells truth
leda_truth = sal_truth  # Leda says Sal tells truth
rashida_truth = leda_truth  # Rashida says Leda tells truth
alejandro_truth = rashida_truth  # Alejandro says Rashida tells truth

print(alejandro_truth)
print("<<<Yes>>>" if alejandro_truth else "<<<No>>>")