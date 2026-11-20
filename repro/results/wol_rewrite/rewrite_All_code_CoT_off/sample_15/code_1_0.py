# Step-by-step logic simulation
brandt_fabricates = True
mercer_accurate = brandt_fabricates  # Mercer says Brandt fabricates (true)
pell_fabricates = mercer_accurate    # Pell says Mercer fabricates (false)
crane_fabricates = pell_fabricates   # Crane says Pell accurate (false)
halloway_fabricates = crane_fabricates  # Halloway says Crane accurate (false)
voss_accurate = halloway_fabricates  # Voss says Halloway fabricates (true)
sable_fabricates = voss_accurate     # Sable says Voss fabricates (false)

crane_accurate = not crane_fabricates
print(crane_accurate)