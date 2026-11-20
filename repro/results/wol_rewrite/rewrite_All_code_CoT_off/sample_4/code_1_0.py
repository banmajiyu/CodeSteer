grimm_fabricates = True
mercer_says_grimm_accurate = not grimm_fabricates  # False
mercer_fabricates = not mercer_says_grimm_accurate  # True
holt_says_mercer_fabricates = mercer_fabricates  # True
holt_accurate = holt_says_mercer_fabricates  # True

print("Does Clerk Holt report accurately?", "<<<Yes>>>" if holt_accurate else "<<<No>>>")