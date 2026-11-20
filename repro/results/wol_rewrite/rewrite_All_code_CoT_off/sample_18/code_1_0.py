# Step-by-step logic simulation
brandt_accurate = True
odell_accurate = not brandt_accurate  # Odell says Brandt fabricates
ives_accurate = not odell_accurate    # Ives says Odell fabricates
kessler_accurate = ives_accurate      # Kessler says Ives reports accurately
holt_accurate = not kessler_accurate  # Holt says Kessler fabricates
rowe_accurate = not holt_accurate     # Rowe says Holt fabricates

print(kessler_accurate)