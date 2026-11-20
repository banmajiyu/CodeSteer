# Durand is truthful
durand_truthful = True

# Rowe says Durand fabricates -> false statement
rowe_truthful = not durand_truthful  # False

# Mercer says Rowe truthful -> false statement
mercer_truthful = rowe_truthful  # False

# Fisk says Mercer truthful -> false statement
fisk_truthful = mercer_truthful  # False

# Kessler says Fisk truthful -> false statement
kessler_truthful = fisk_truthful  # False

print("Does Clerk Fisk report accurately?", fisk_truthful)