# Step-by-step truth values
ellery_lies = True
vance_truth = ellery_lies  # Vance says Ellery fabricates (true statement)
winslow_truth = not vance_truth  # Winslow says Vance fabricates (false)
voss_truth = not winslow_truth  # Voss says Winslow fabricates (true)
durand_truth = not voss_truth  # Durand says Voss fabricates (false)
odell_truth = not durand_truth  # Odell says Durand fabricates (true)

print("Durand reports accurately:", durand_truth)
print("<<<" + ("Yes" if durand_truth else "No") + ">>>")