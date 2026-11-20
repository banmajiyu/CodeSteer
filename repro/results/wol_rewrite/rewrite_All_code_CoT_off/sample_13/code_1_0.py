# Step-by-step logic
ellery_accurate = True
brandt_accurate = ellery_accurate  # Brandt says Ellery is accurate
sable_accurate = not brandt_accurate  # Sable says Brandt fabricates
adair_accurate = sable_accurate  # Adair says Sable is accurate
mercer_accurate = adair_accurate  # Mercer says Adair is accurate

print("Mercer reports accurately:", mercer_accurate)
print("<<<" + ("Yes" if mercer_accurate else "No") + ">>>")