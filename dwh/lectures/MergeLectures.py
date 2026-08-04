import os
import pandas as pd

print(os.getcwd())
# === CONFIGURATION ===
# Full-year re-export from TimeEdit (semester 1 + semester 2). data/archived
# now holds the complete run (2025-07-07 through 2026-08-02); data/incoming
# was merged in and removed since it was a strict subset.
dir1 = "data/archived"
output_file = "dwh/lectures/AllLectures.csv"

# === FUNCTION TO READ ALL CSV FILES FROM A DIRECTORY ===
def read_all_csv_from_dir(directory):
    csv_files = [f for f in os.listdir(directory) if f.lower().endswith(".csv")]
    dfs = []
    for file in csv_files:
        path = os.path.join(directory, file)
        try:
            df = pd.read_csv(path)
            dfs.append(df)
            print(f"✅ Loaded {file} ({len(df)} rows)")
        except Exception as e:
            print(f"⚠️  Skipped {file} — {e}")
    return dfs

# === LOAD DATA ===
all_dfs = read_all_csv_from_dir(dir1)

if not all_dfs:
    print("❌ No CSV files found in either directory.")
else:
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(output_file, index=False)
    print(f"\n✅ Successfully merged {len(all_dfs)} files.")
    print(f"💾 Output saved to: {output_file}")
