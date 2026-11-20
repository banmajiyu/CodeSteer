# Step-by-step truth evaluation
delfina_truth = True
fletcher_truth = not delfina_truth  # Fletcher says Delfina lies
amberly_truth = not fletcher_truth  # Amberly says Fletcher lies
audrie_truth = amberly_truth        # Audrie says Amberly tells truth
lorine_truth = audrie_truth         # Lorine says Audrie tells truth

print("Delfina:", delfina_truth)
print("Fletcher:", fletcher_truth)
print("Amberly:", amberly_truth)
print("Audrie:", audrie_truth)
print("Lorine:", lorine_truth)

if lorine_truth:
    print("<<<Yes>>>")
else:
    print("<<<No>>>")