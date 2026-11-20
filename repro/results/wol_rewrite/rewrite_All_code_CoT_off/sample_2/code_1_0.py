# 1 = accurate, 0 = fabricates
Fisk = 1  # given

# Tobias says Fisk fabricates (Fisk == 0)
Tobias_statement = (Fisk == 0)
# Tobias is accurate if his statement matches reality
Tobias = 1 if Tobias_statement == (Fisk == 0) else 0
# But more directly: Tobias's statement is False, so Tobias fabricates
Tobias = 0

# Brandt says Tobias fabricates (Tobias == 0)
Brandt_statement = (Tobias == 0)
Brandt = 1 if Brandt_statement else 0

# Grimm says Brandt fabricates (Brandt == 0)
Grimm_statement = (Brandt == 0)
Grimm = 1 if Grimm_statement else 0

# Halloway says Grimm reports accurately (Grimm == 1)
Halloway_statement = (Grimm == 1)
Halloway = 1 if Halloway_statement else 0

print("Tobias accurate?", "Yes" if Tobias == 1 else "No")