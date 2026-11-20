# Given: Sable reports accurately
sable_accurate = True

# Rune says Sable fabricates
rune_statement = not sable_accurate  # False, since Sable is accurate
rune_accurate = rune_statement  # Rune's accuracy matches truth of his statement
# rune_accurate is False

# Ives says Rune fabricates
ives_statement = not rune_accurate  # True
ives_accurate = ives_statement  # True

# Pell says Ives reports accurately
pell_statement = ives_accurate  # True
pell_accurate = pell_statement  # True

# Kessler says Pell fabricates
kessler_statement = not pell_accurate  # False
kessler_accurate = kessler_statement  # False

print("Does Clerk Rune report accurately?", rune_accurate)
print("<<<" + ("Yes" if rune_accurate else "No") + ">>>")