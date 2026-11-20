# Truth values: True = accurate, False = fabricates
grimm = True
holt = grimm  # Holt says Grimm is accurate
fisk = holt   # Fisk says Holt is accurate
tobias = not fisk  # Tobias says Fisk fabricates
adair = tobias  # Adair says Tobias is accurate

print("Holt reports accurately:", holt)
print("<<<Yes>>>" if holt else "<<<No>>>")