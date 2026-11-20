# Truth values: True = accurate, False = fabricates
odell = True  # given
winslow = not odell  # Winslow says Odell fabricates -> false since Odell truthful
voss = not winslow   # Voss says Winslow fabricates -> true
tobias = voss        # Tobias says Voss accurate
pell = tobias        # Pell says Tobias accurate
ives = not pell      # Ives says Pell fabricates

print(ives)  # False means Ives does not report accurately