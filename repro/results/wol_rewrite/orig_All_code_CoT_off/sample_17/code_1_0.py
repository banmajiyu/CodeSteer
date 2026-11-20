# Step-by-step truth evaluation
ka_lies = True  # given

# Andree says Ka tells the truth
andree_truth = not ka_lies  # Andree is lying if Ka lies
# Audrie says Andree lies
audrie_truth = not andree_truth
# Antwan says Audrie tells the truth
antwan_truth = audrie_truth
# Millie says Antwan tells the truth
millie_truth = antwan_truth

print("Andree tells truth:", andree_truth)
print("Audrie tells truth:", audrie_truth)
print("Antwan tells truth:", antwan_truth)
print("Millie tells truth:", millie_truth)

if millie_truth:
    print("<<<Yes>>>")
else:
    print("<<<No>>>")