# Step-by-step logic simulation
# True = reports accurately, False = fabricates

# Durand reports accurately
durand = True

# Tobias says Durand reports accurately
tobias = (durand == True)

# Crane says Tobias reports accurately
crane = (tobias == True)

# Fisk says Crane fabricates
fisk = (crane == False)

# Grimm says Fisk fabricates
grimm = (fisk == False)

# Brandt says Grimm reports accurately
brandt = (grimm == True)

# Does Tobias report accurately?
print("Yes" if tobias else "No")