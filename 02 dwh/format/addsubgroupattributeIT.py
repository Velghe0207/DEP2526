from pathlib import Path
import pandas as pd


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"D:\Documents2\School\26-EP3\DEP\repo"
    r"\DEP2-2025-2026-groep12\00 data"
)

INPUT_CSV = (
    BASE_DIR
    / "raw"
    / "subgroups"
    / "all_subgroups_enriched.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "cleaned"
    / "all_subgroups_final.csv"
)

REVIEW_CSV = (
    BASE_DIR
    / "cleaned"
    / "subgroups_unknown_studyprogram.csv"
)


# ============================================================
# 2. PROGRAM MAPPING
# ============================================================

# De sleutels zijn mogelijke ProgramFamily- of ProgramName-prefixen.
# Je kunt deze dictionary later uitbreiden.
PROGRAM_MAPPING = {
    "PBA-TIN": "Toegepaste Informatica",
    "PBA-SO": "Sociaal Werk",
    "PBA-VPK": "Verpleegkunde",
    "PBA-VOE": "Voedings- en Dieetkunde",
    "PBA-ERGO": "Ergotherapie",
    "PBA-LO": "Lager Onderwijs",
    "PBA-KO": "Kleuteronderwijs",
    "PBA-SOLO": "Secundair Onderwijs",
}

# Extra waarden die expliciet als IT beschouwd moeten worden.
IT_PATTERNS = [
    "PBA-TIN",
    "TOEGEPASTE INFORMATICA",
    "APPLIED COMPUTER SCIENCE",
    "IC IT",
]


# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Zet lege waarden om naar pd.NA en verwijdert spaties."""
    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if value.lower() in {"", "nan", "none", "<na>"}:
        return pd.NA

    return value


def extract_program_family(program_name):
    """
    Haalt de algemene programmacode uit ProgramName.

    Voorbeelden:
    PBA-TIN/1A       -> PBA-TIN
    PBA-TIN/AI/3A    -> PBA-TIN
    PBA-SO/LOBR/2A   -> PBA-SO
    """
    program_name = clean_text(program_name)

    if pd.isna(program_name):
        return pd.NA

    return program_name.split("/")[0].strip().upper()


def determine_program_family(row):
    """
    Gebruikt eerst de bestaande ProgramFamily.
    Als die ontbreekt, wordt ze afgeleid uit ProgramName.
    """
    existing_family = clean_text(row.get("ProgramFamily"))

    if pd.notna(existing_family):
        return str(existing_family).upper()

    return extract_program_family(row.get("ProgramName"))


def determine_study_program(row):
    """
    Zet ProgramFamily of ProgramName om naar een leesbare opleiding.
    """
    program_family = clean_text(row.get("ProgramFamily"))
    program_name = clean_text(row.get("ProgramName"))

    values_to_check = [
        program_family,
        program_name,
    ]

    for value in values_to_check:
        if pd.isna(value):
            continue

        normalized_value = str(value).upper()

        # Zoek eerst een expliciete prefix uit de mapping
        for program_code, study_program in PROGRAM_MAPPING.items():
            if normalized_value.startswith(program_code):
                return study_program

        # Extra herkenning voor IT-benamingen
        if any(
            pattern in normalized_value
            for pattern in IT_PATTERNS
        ):
            return "Toegepaste Informatica"

    return pd.NA


def determine_is_it(row):
    """
    Bepaalt of een subgroep bij Toegepaste Informatica hoort.

    Zowel ProgramName, ProgramFamily als StudyProgram worden gebruikt.
    """
    values_to_check = [
        row.get("ProgramName"),
        row.get("ProgramFamily"),
        row.get("StudyProgram"),
    ]

    for value in values_to_check:
        value = clean_text(value)

        if pd.isna(value):
            continue

        normalized_value = str(value).upper()

        if any(
            pattern in normalized_value
            for pattern in IT_PATTERNS
        ):
            return True

    return False


def determine_program_information_level(row):
    """
    Geeft aan hoe volledig de programmagegevens zijn.
    """
    has_program_name = pd.notna(
        clean_text(row.get("ProgramName"))
    )

    has_program_family = pd.notna(
        clean_text(row.get("ProgramFamily"))
    )

    if has_program_name:
        return "ExactProgramName"

    if has_program_family:
        return "ProgramFamilyOnly"

    return "Unknown"


# ============================================================
# 4. LOAD DATA
# ============================================================

if not INPUT_CSV.exists():
    raise FileNotFoundError(
        f"Inputbestand niet gevonden:\n{INPUT_CSV}"
    )

df = pd.read_csv(
    INPUT_CSV,
    sep=";",
    dtype="string",
    encoding="utf-8-sig",
)

df.columns = df.columns.str.strip()

required_columns = [
    "SubgroupKey",
    "SubgroupCode",
    "ProgramName",
    "ProgramFamily",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise KeyError(
        "De volgende verplichte kolommen ontbreken:\n"
        + "\n".join(f"- {column}" for column in missing_columns)
    )

print(f"Inputbestand gelezen: {len(df):,} subgroepen")


# ============================================================
# 5. CLEAN EXISTING COLUMNS
# ============================================================

df["SubgroupCode"] = (
    df["SubgroupCode"]
    .astype("string")
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

df["ProgramName"] = df["ProgramName"].apply(clean_text)
df["ProgramFamily"] = df["ProgramFamily"].apply(clean_text)


# ============================================================
# 6. COMPLETE PROGRAMFAMILY
# ============================================================

# Vul een ontbrekende ProgramFamily aan op basis van ProgramName.
df["ProgramFamily"] = df.apply(
    determine_program_family,
    axis=1,
)


# ============================================================
# 7. CREATE STUDYPROGRAM
# ============================================================

df["StudyProgram"] = df.apply(
    determine_study_program,
    axis=1,
)


# ============================================================
# 8. CREATE ISIT
# ============================================================

df["IsIT"] = df.apply(
    determine_is_it,
    axis=1,
).astype(bool)


# ============================================================
# 9. ADD INFORMATION LEVEL
# ============================================================

df["ProgramInformationLevel"] = df.apply(
    determine_program_information_level,
    axis=1,
)


# ============================================================
# 10. REORDER COLUMNS
# ============================================================

preferred_columns = [
    "SubgroupKey",
    "SubgroupCode",
    "ProgramName",
    "ProgramFamily",
    "StudyProgram",
    "IsIT",
    "ProgramInformationLevel",
    "ProgramNameSource",
    "ProgramFamilySource",
    "InferenceConfidence",
    "InferenceEvidenceCount",
]

final_columns = [
    column
    for column in preferred_columns
    if column in df.columns
]

remaining_columns = [
    column
    for column in df.columns
    if column not in final_columns
]

df = df[final_columns + remaining_columns]


# ============================================================
# 11. VALIDATION
# ============================================================

duplicate_subgroup_keys = df["SubgroupKey"].duplicated().sum()
duplicate_subgroup_codes = df["SubgroupCode"].duplicated().sum()

if duplicate_subgroup_keys:
    raise ValueError(
        f"Er zijn {duplicate_subgroup_keys:,} dubbele SubgroupKeys."
    )

if duplicate_subgroup_codes:
    raise ValueError(
        f"Er zijn {duplicate_subgroup_codes:,} dubbele SubgroupCodes."
    )


# ============================================================
# 12. SAVE OUTPUT
# ============================================================

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUTPUT_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

# Bewaar onbekende programma's afzonderlijk voor eventuele controle.
unknown_df = df[
    df["StudyProgram"].isna()
].copy()

unknown_df.to_csv(
    REVIEW_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 13. PRINT SUMMARY
# ============================================================

total_subgroups = len(df)
it_subgroups = df["IsIT"].sum()
non_it_subgroups = (~df["IsIT"]).sum()
known_study_program = df["StudyProgram"].notna().sum()
unknown_study_program = df["StudyProgram"].isna().sum()

print("\n" + "=" * 70)
print("FINAL SUBGROUP FILE CREATED")
print("=" * 70)

print(f"Totaal aantal subgroepen:       {total_subgroups:,}")
print(f"Als IT geclassificeerd:         {it_subgroups:,}")
print(f"Niet als IT geclassificeerd:    {non_it_subgroups:,}")
print(f"Met gekende StudyProgram:       {known_study_program:,}")
print(f"Zonder gekende StudyProgram:    {unknown_study_program:,}")

if total_subgroups > 0:
    print(
        f"IT-percentage:                  "
        f"{it_subgroups / total_subgroups * 100:.2f}%"
    )

print("\nProgram information levels:")
print(
    df["ProgramInformationLevel"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nStudyProgram-verdeling:")
print(
    df["StudyProgram"]
    .value_counts(dropna=False)
    .to_string()
)

print(f"\n✅ Definitief subgroepenbestand:\n{OUTPUT_CSV}")
print(f"\n❓ Onbekende opleidingen ter controle:\n{REVIEW_CSV}")