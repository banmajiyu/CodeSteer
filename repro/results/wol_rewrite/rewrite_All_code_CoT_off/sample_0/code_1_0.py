# Truth-teller = True, Liar = False
Durand = True  # given
Holt = Durand  # Holt says Durand is accurate
Brandt = not Holt  # Brandt says Holt fabricates
Voss = Brandt  # Voss says Brandt is accurate
Halloway = not Voss  # Halloway says Voss fabricates
Sable = Halloway  # Sable says Halloway is accurate

print(Sable)
print("Yes" if Sable else "No")