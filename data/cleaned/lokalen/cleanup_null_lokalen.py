import pandas as pd

# Read the CSV file
df = pd.read_csv("./alle_lokalen.csv")

# Remove rows where Capacity is NULL (string 'NULL' or actual NaN)
df_cleaned = df[df["Capacity"].notnull() & (df["Capacity"] != "NULL")]

# Save the cleaned data to a new CSV file
df_cleaned.to_csv("lokalen_cleaned.csv", index=False)

print(f"Cleaned file saved as 'lokalen_cleaned.csv' with {len(df_cleaned)} rows.")
