# Step-by-step logic
ellery_fabricates = True
mercer_accurate = ellery_fabricates  # Mercer says Ellery fabricates (true)
holt_fabricates = not mercer_accurate  # Holt says Mercer fabricates (false)
jarvis_accurate = holt_fabricates  # Jarvis says Holt fabricates (true)
winslow_fabricates = not jarvis_accurate  # Winslow says Jarvis fabricates (false)
durand_fabricates = not (not winslow_fabricates)  # Durand says Winslow accurate (false)
adair_accurate = durand_fabricates  # Adair says Durand fabricates (true)

print("Jarvis reports accurately:", jarvis_accurate)
print("<<<Yes>>>" if jarvis_accurate else "<<<No>>>")