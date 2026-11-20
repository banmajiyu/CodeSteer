# Step-by-step logic simulation
sable_accurate = False  # given
adair_accurate = sable_accurate  # Adair says Sable is accurate
rune_accurate = adair_accurate    # Rune says Adair is accurate
odell_accurate = not rune_accurate  # Odell says Rune fabricates
tobias_accurate = not odell_accurate  # Tobias says Odell fabricates

print(adair_accurate)