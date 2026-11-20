# Truth values: True means tells truth, False means lies
willian = False  # given
inga = willian   # Inga says Willian tells truth, so Inga's truth value equals Willian's
fidel = not inga # Fidel says Inga lies
gwenn = fidel    # Gwenn says Fidel tells truth
crista = gwenn   # Crista says Gwenn tells truth

print("Willian:", willian)
print("Inga:", inga)
print("Fidel:", fidel)
print("Gwenn:", gwenn)
print("Crista:", crista)

if crista:
    print("<<<Yes>>>")
else:
    print("<<<No>>>")