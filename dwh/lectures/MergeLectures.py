import os
import pandas as pd

print(os.getcwd())
# === CONFIGURATION ===
dir1 = "data/archived"
dir2 = "data/incoming"
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
dfs_dir1 = read_all_csv_from_dir(dir1)
dfs_dir2 = read_all_csv_from_dir(dir2)

# === MERGE ALL ===
all_dfs = dfs_dir1 + dfs_dir2

if not all_dfs:
    print("❌ No CSV files found in either directory.")
else:
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_df.to_csv(output_file, index=False)
    print(f"\n✅ Successfully merged {len(all_dfs)} files.")
    print(f"💾 Output saved to: {output_file}")
