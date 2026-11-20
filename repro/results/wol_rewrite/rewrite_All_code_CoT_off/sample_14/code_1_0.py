# Step-by-step evaluation
brandt_accurate = True
winslow_accurate = brandt_accurate  # Winslow says Brandt accurate
holt_accurate = winslow_accurate    # Holt says Winslow accurate
mercer_accurate = not holt_accurate # Mercer says Holt fabricates
tobias_accurate = not mercer_accurate  # Tobias says Mercer fabricates
crane_accurate = tobias_accurate    # Crane says Tobias accurate
ellery_accurate = crane_accurate    # Ellery says Crane accurate

print(mercer_accurate)