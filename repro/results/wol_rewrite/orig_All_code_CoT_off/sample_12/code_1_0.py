# Step-by-step truth evaluation
millie_truth = True  # given
millicent_truth = not millie_truth  # Millicent says Millie lies, so opposite of Millie's truth
phoebe_truth = millicent_truth  # Phoebe says Millicent tells truth
sherrie_truth = not phoebe_truth  # Sherrie says Phoebe lies
raymond_truth = sherrie_truth  # Raymond says Sherrie tells truth

print("Millie:", millie_truth)
print("Millicent:", millicent_truth)
print("Phoebe:", phoebe_truth)
print("Sherrie:", sherrie_truth)
print("Raymond:", raymond_truth)

if raymond_truth:
    print("<<<Yes>>>")
else:
    print("<<<No>>>")