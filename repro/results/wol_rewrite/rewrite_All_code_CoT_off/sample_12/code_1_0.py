# Truth-teller = True, Liar = False
crane = True  # given
adair = not crane  # Adair says Crane fabricates
jarvis = not adair  # Jarvis says Adair fabricates
vance = not jarvis  # Vance says Jarvis fabricates
tobias = not vance  # Tobias says Vance fabricates

print("Yes" if tobias else "No")