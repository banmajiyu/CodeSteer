# Step-by-step logic simulation
brandt_accurate = False  # given: Brandt fabricates

# Tobias says Brandt is accurate
tobias_statement = brandt_accurate  # False
# Tobias must be fabricator if statement is false
tobias_accurate = tobias_statement  # False

# Fisk says Tobias fabricates
fisk_statement = not tobias_accurate  # True
fisk_accurate = fisk_statement  # True

# Halloway says Fisk is accurate
halloway_statement = fisk_accurate  # True
halloway_accurate = halloway_statement  # True

# Pell says Halloway is accurate
pell_statement = halloway_accurate  # True
pell_accurate = pell_statement  # True

print("Does Tobias report accurately?", "<<<Yes>>>" if tobias_accurate else "<<<No>>>")