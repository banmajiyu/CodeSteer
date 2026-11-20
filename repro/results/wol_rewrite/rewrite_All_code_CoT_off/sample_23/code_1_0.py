# Truth values: True = reports accurately, False = fabricates
ellery = False  # given

# Adair says Ellery reports accurately
adair_statement = ellery  # this is False
adair = adair_statement  # Adair's truthfulness equals truth of their statement
# Since adair_statement is False, adair is False (fabricates)

# Fisk says Adair fabricates
fisk_statement = not adair  # True, since adair is False
fisk = fisk_statement  # True

# Voss says Fisk reports accurately
voss_statement = fisk  # True
voss = voss_statement  # True

print(adair)  # False means Adair does not report accurately