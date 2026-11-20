# 0 = fabricates, 1 = reports accurately
jarvis = 0  # given

# Voss says Jarvis reports accurately
voss = 1 if jarvis == 1 else 0

# Winslow says Voss reports accurately
winslow = 1 if voss == 1 else 0

# Grimm says Winslow fabricates
grimm = 1 if winslow == 0 else 0

# Mercer says Grimm reports accurately
mercer = 1 if grimm == 1 else 0

# Ives says Mercer fabricates
ives = 1 if mercer == 0 else 0

# Rowe says Ives fabricates
rowe = 1 if ives == 0 else 0

print("Jarvis:", jarvis)
print("Voss:", voss)
print("Winslow:", winslow)
print("Grimm:", grimm)
print("Mercer:", mercer)
print("Ives:", ives)
print("Rowe:", rowe)

print("Does Mercer report accurately?", "Yes" if mercer == 1 else "No")