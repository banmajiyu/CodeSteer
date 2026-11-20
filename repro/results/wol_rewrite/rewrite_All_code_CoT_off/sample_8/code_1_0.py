# Given: Adair fabricates
adair_fabricates = True

# Odell says Adair fabricates
odell_statement = adair_fabricates  # True if Adair fabricates
odell_accurate = odell_statement  # Odell's statement matches reality

print("Does Clerk Odell report accurately?", "<<<Yes>>>" if odell_accurate else "<<<No>>>")