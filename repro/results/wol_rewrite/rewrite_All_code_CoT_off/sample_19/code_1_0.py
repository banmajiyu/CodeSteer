holt_fabricates = True
fisk_accurate = not holt_fabricates  # Fisk says Holt accurate, but Holt fabricates → Fisk lies
halloway_accurate = fisk_accurate    # Halloway says Fisk accurate, but Fisk lies → Halloway lies
mercer_accurate = not halloway_accurate  # Mercer says Halloway fabricates → true if Halloway lies
print(mercer_accurate)