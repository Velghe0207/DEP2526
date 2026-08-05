import pandas as pd

# Bestand inlezen
input_file = r"D:\Documents2\School\26-EP3\DEP\repo\DEP2-2025-2026-groep12\data\cleaned\all_courses.csv"

# Overschrijf hetzelfde bestand of kies een nieuw pad
output_file = input_file
# output_file = r"D:\Documents2\School\26-EP3\DEP\repo\DEP2-2025-2026-groep12\data\cleaned\all_courses_TI.csv"

# CSV inlezen
df = pd.read_csv(input_file, delimiter=",")

# Zoek de kolom waarin de opleiding staat
# (pas eventueel de kolomnaam aan indien nodig)
opleiding_kolom = df.columns[1]

# Enkel Toegepaste Informatica behouden
df = df[
    df["faculties"]
    .fillna("")
    .str.lower()
    .str.contains("toegepaste informatica")
]

# Opslaan
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"Klaar! {len(df)} rijen overgehouden.")