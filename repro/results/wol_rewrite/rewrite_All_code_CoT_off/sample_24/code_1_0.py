# Step-by-step logic
kessler_fabricates = True
rowe_accurate = kessler_fabricates  # Rowe says Kessler fabricates, which is true
odell_accurate = not rowe_accurate  # Odell says Rowe fabricates, which is false
grimm_accurate = odell_accurate     # Grimm says Odell accurate, but Odell is not
tobias_accurate = grimm_accurate    # Tobias says Grimm accurate, but Grimm is not

print("Does Clerk Odell report accurately?", "<<<Yes>>>" if odell_accurate else "<<<No>>>")