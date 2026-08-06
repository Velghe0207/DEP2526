import csv
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"D:\Documents2\School\26-EP3\DEP\repo"
    r"\DEP2-2025-2026-groep12\00 data\raw"
)

SUBGROUPS_CSV = (
    BASE_DIR
    / "subgroups"
    / "all_subgroups.csv"
)

LECTURES_CSV = (
    BASE_DIR
    / "lectures"
    / "AllLectures.csv"
)

OUTPUT_CSV = (
    BASE_DIR
    / "subgroups"
    / "all_subgroups_enriched.csv"
)

EVIDENCE_CSV = (
    BASE_DIR
    / "subgroups"
    / "subgroup_cooccurrence_evidence.csv"
)

UNRESOLVED_CSV = (
    BASE_DIR
    / "subgroups"
    / "subgroups_still_missing_programname.csv"
)

# Minimaal aantal verschillende lectures waarin dezelfde conclusie
# terugkomt.
MIN_LECTURE_EVIDENCE = 3

# Minimaal aandeel van de populairste kandidaat.
MIN_CONFIDENCE = 0.80


# ============================================================
# HELPERS
# ============================================================

def detect_separator(file_path: Path) -> str:
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
    ) as file:
        sample = file.read(8192)

    try:
        return csv.Sniffer().sniff(
            sample,
            delimiters=";,\t",
        ).delimiter
    except csv.Error:
        return ";"


def read_csv_auto(file_path: Path) -> pd.DataFrame:
    separator = detect_separator(file_path)

    df = pd.read_csv(
        file_path,
        sep=separator,
        dtype="string",
        encoding="utf-8-sig",
        engine="python",
        on_bad_lines="warn",
    )

    df.columns = df.columns.str.strip()

    print(
        f"✅ {file_path.name}: "
        f"{len(df):,} rijen, separator={repr(separator)}"
    )

    return df


def normalize_id(series: pd.Series) -> pd.Series:
    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def clean_text(series: pd.Series) -> pd.Series:
    return (
        series
        .astype("string")
        .str.strip()
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )


def split_pipe_values(value) -> list[str]:
    if pd.isna(value):
        return []

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


def get_program_family(program_name):
    """
    Voorbeelden:
    PBA-TIN/2A       -> PBA-TIN
    PBA-TIN/AI/3A    -> PBA-TIN
    PBA-SO/LOBR/2A   -> PBA-SO
    """
    if pd.isna(program_name):
        return pd.NA

    parts = str(program_name).strip().split("/")

    return parts[0] if parts else pd.NA


# ============================================================
# LOAD SUBGROUPS
# ============================================================

subgroups_df = read_csv_auto(SUBGROUPS_CSV)

required_subgroup_columns = [
    "SubgroupKey",
    "SubgroupCode",
    "ProgramName",
]

missing_columns = [
    column
    for column in required_subgroup_columns
    if column not in subgroups_df.columns
]

if missing_columns:
    raise KeyError(
        "Ontbrekende kolommen in all_subgroups.csv:\n"
        + "\n".join(f"- {column}" for column in missing_columns)
    )

subgroups_df["SubgroupCode"] = normalize_id(
    subgroups_df["SubgroupCode"]
)

subgroups_df["ProgramName"] = clean_text(
    subgroups_df["ProgramName"]
)

subgroups_df["ProgramFamily"] = (
    subgroups_df["ProgramName"]
    .apply(get_program_family)
)

subgroups_df["ProgramNameSource"] = pd.NA
subgroups_df["ProgramFamilySource"] = pd.NA
subgroups_df["InferenceConfidence"] = pd.NA
subgroups_df["InferenceEvidenceCount"] = pd.NA

known_mask = subgroups_df["ProgramName"].notna()

subgroups_df.loc[
    known_mask,
    "ProgramNameSource",
] = "students"

subgroups_df.loc[
    known_mask,
    "ProgramFamilySource",
] = "students"


# ============================================================
# LOAD AND EXPLODE LECTURES
# ============================================================

lectures_df = read_csv_auto(LECTURES_CSV)

if "Id" not in lectures_df.columns:
    raise KeyError("Kolom 'Id' ontbreekt in AllLectures.csv.")

if "Classgroups" not in lectures_df.columns:
    raise KeyError(
        "Kolom 'Classgroups' ontbreekt in AllLectures.csv."
    )

lecture_groups_df = lectures_df[
    [
        "Id",
        "Classgroups",
    ]
].copy()

lecture_groups_df["SubgroupCode"] = (
    lecture_groups_df["Classgroups"]
    .apply(split_pipe_values)
)

lecture_groups_df = lecture_groups_df.explode(
    "SubgroupCode",
    ignore_index=True,
)

lecture_groups_df["SubgroupCode"] = normalize_id(
    lecture_groups_df["SubgroupCode"]
)

lecture_groups_df = lecture_groups_df[
    lecture_groups_df["SubgroupCode"].notna()
].copy()

lecture_groups_df = lecture_groups_df.drop_duplicates(
    subset=[
        "Id",
        "SubgroupCode",
    ]
)

print("\n=== LECTURE-SUBGROUP LINKS ===")
print(f"Links:             {len(lecture_groups_df):,}")
print(
    f"Unieke lectures:   "
    f"{lecture_groups_df['Id'].nunique():,}"
)
print(
    f"Unieke subgroepen: "
    f"{lecture_groups_df['SubgroupCode'].nunique():,}"
)


# ============================================================
# ATTACH KNOWN PROGRAM INFORMATION
# ============================================================

known_programs_df = (
    subgroups_df[
        subgroups_df["ProgramName"].notna()
    ][
        [
            "SubgroupCode",
            "ProgramName",
            "ProgramFamily",
        ]
    ]
    .drop_duplicates(subset=["SubgroupCode"])
)

lecture_groups_df = lecture_groups_df.merge(
    known_programs_df,
    how="left",
    on="SubgroupCode",
    validate="many_to_one",
)


# ============================================================
# BUILD LECTURE-LEVEL PROGRAM VOTES
# ============================================================

# Bepaal per lecture welke ProgramNames van gekende subgroepen
# aanwezig zijn.
lecture_program_votes = (
    lecture_groups_df[
        lecture_groups_df["ProgramName"].notna()
    ][
        [
            "Id",
            "ProgramName",
        ]
    ]
    .drop_duplicates()
)

lecture_family_votes = (
    lecture_groups_df[
        lecture_groups_df["ProgramFamily"].notna()
    ][
        [
            "Id",
            "ProgramFamily",
        ]
    ]
    .drop_duplicates()
)


# ============================================================
# FIND MISSING SUBGROUPS IN THE SAME LECTURES
# ============================================================

missing_codes = set(
    subgroups_df.loc[
        subgroups_df["ProgramName"].isna(),
        "SubgroupCode",
    ].dropna()
)

missing_lecture_groups = lecture_groups_df[
    lecture_groups_df["SubgroupCode"].isin(
        missing_codes
    )
][
    [
        "Id",
        "SubgroupCode",
    ]
].drop_duplicates()


# ============================================================
# EXACT PROGRAMNAME CANDIDATES
# ============================================================

exact_candidates = missing_lecture_groups.merge(
    lecture_program_votes,
    how="inner",
    on="Id",
    validate="many_to_many",
)

# Elke lecture telt maximaal één keer als stem voor een kandidaat.
exact_candidates = exact_candidates.drop_duplicates(
    subset=[
        "Id",
        "SubgroupCode",
        "ProgramName",
    ]
)

exact_counts = (
    exact_candidates
    .groupby(
        [
            "SubgroupCode",
            "ProgramName",
        ]
    )
    .size()
    .reset_index(name="EvidenceCount")
)

exact_totals = (
    exact_counts
    .groupby("SubgroupCode")["EvidenceCount"]
    .sum()
    .rename("TotalEvidence")
    .reset_index()
)

exact_counts = exact_counts.merge(
    exact_totals,
    on="SubgroupCode",
    how="left",
)

exact_counts["Confidence"] = (
    exact_counts["EvidenceCount"]
    / exact_counts["TotalEvidence"]
)

exact_counts = exact_counts.sort_values(
    by=[
        "SubgroupCode",
        "EvidenceCount",
        "ProgramName",
    ],
    ascending=[
        True,
        False,
        True,
    ],
)

best_exact = (
    exact_counts
    .drop_duplicates(
        subset=["SubgroupCode"],
        keep="first",
    )
    .copy()
)


# ============================================================
# DETECT TIES FOR EXACT PROGRAMNAME
# ============================================================

top_exact_votes = (
    exact_counts
    .groupby("SubgroupCode")["EvidenceCount"]
    .max()
    .rename("TopEvidenceCount")
    .reset_index()
)

exact_ties = exact_counts.merge(
    top_exact_votes,
    on="SubgroupCode",
    how="left",
)

exact_ties = (
    exact_ties[
        exact_ties["EvidenceCount"]
        == exact_ties["TopEvidenceCount"]
    ]
    .groupby("SubgroupCode")
    .size()
    .rename("TopCandidateCount")
    .reset_index()
)

best_exact = best_exact.merge(
    exact_ties,
    on="SubgroupCode",
    how="left",
)

best_exact["CanInferExact"] = (
    (
        best_exact["EvidenceCount"]
        >= MIN_LECTURE_EVIDENCE
    )
    & (
        best_exact["Confidence"]
        >= MIN_CONFIDENCE
    )
    & (
        best_exact["TopCandidateCount"] == 1
    )
)


# ============================================================
# PROGRAMFAMILY CANDIDATES
# ============================================================

family_candidates = missing_lecture_groups.merge(
    lecture_family_votes,
    how="inner",
    on="Id",
    validate="many_to_many",
)

family_candidates = family_candidates.drop_duplicates(
    subset=[
        "Id",
        "SubgroupCode",
        "ProgramFamily",
    ]
)

family_counts = (
    family_candidates
    .groupby(
        [
            "SubgroupCode",
            "ProgramFamily",
        ]
    )
    .size()
    .reset_index(name="EvidenceCount")
)

family_totals = (
    family_counts
    .groupby("SubgroupCode")["EvidenceCount"]
    .sum()
    .rename("TotalEvidence")
    .reset_index()
)

family_counts = family_counts.merge(
    family_totals,
    on="SubgroupCode",
    how="left",
)

family_counts["Confidence"] = (
    family_counts["EvidenceCount"]
    / family_counts["TotalEvidence"]
)

family_counts = family_counts.sort_values(
    by=[
        "SubgroupCode",
        "EvidenceCount",
        "ProgramFamily",
    ],
    ascending=[
        True,
        False,
        True,
    ],
)

best_family = (
    family_counts
    .drop_duplicates(
        subset=["SubgroupCode"],
        keep="first",
    )
    .copy()
)

top_family_votes = (
    family_counts
    .groupby("SubgroupCode")["EvidenceCount"]
    .max()
    .rename("TopEvidenceCount")
    .reset_index()
)

family_ties = family_counts.merge(
    top_family_votes,
    on="SubgroupCode",
    how="left",
)

family_ties = (
    family_ties[
        family_ties["EvidenceCount"]
        == family_ties["TopEvidenceCount"]
    ]
    .groupby("SubgroupCode")
    .size()
    .rename("TopCandidateCount")
    .reset_index()
)

best_family = best_family.merge(
    family_ties,
    on="SubgroupCode",
    how="left",
)

best_family["CanInferFamily"] = (
    (
        best_family["EvidenceCount"]
        >= MIN_LECTURE_EVIDENCE
    )
    & (
        best_family["Confidence"]
        >= MIN_CONFIDENCE
    )
    & (
        best_family["TopCandidateCount"] == 1
    )
)


# ============================================================
# APPLY EXACT PROGRAMNAME INFERENCES
# ============================================================

accepted_exact = best_exact[
    best_exact["CanInferExact"]
][
    [
        "SubgroupCode",
        "ProgramName",
        "Confidence",
        "EvidenceCount",
    ]
].rename(
    columns={
        "ProgramName": "InferredProgramName",
        "Confidence": "ExactConfidence",
        "EvidenceCount": "ExactEvidenceCount",
    }
)

subgroups_df = subgroups_df.merge(
    accepted_exact,
    how="left",
    on="SubgroupCode",
    validate="one_to_one",
)

exact_fill_mask = (
    subgroups_df["ProgramName"].isna()
    & subgroups_df["InferredProgramName"].notna()
)

subgroups_df.loc[
    exact_fill_mask,
    "ProgramName",
] = subgroups_df.loc[
    exact_fill_mask,
    "InferredProgramName",
]

subgroups_df.loc[
    exact_fill_mask,
    "ProgramFamily",
] = (
    subgroups_df.loc[
        exact_fill_mask,
        "InferredProgramName",
    ]
    .apply(get_program_family)
)

subgroups_df.loc[
    exact_fill_mask,
    "ProgramNameSource",
] = "lecture_subgroup_cooccurrence"

subgroups_df.loc[
    exact_fill_mask,
    "ProgramFamilySource",
] = "lecture_subgroup_cooccurrence"

subgroups_df.loc[
    exact_fill_mask,
    "InferenceConfidence",
] = subgroups_df.loc[
    exact_fill_mask,
    "ExactConfidence",
]

subgroups_df.loc[
    exact_fill_mask,
    "InferenceEvidenceCount",
] = subgroups_df.loc[
    exact_fill_mask,
    "ExactEvidenceCount",
]


# ============================================================
# APPLY PROGRAMFAMILY INFERENCES
# ============================================================

accepted_family = best_family[
    best_family["CanInferFamily"]
][
    [
        "SubgroupCode",
        "ProgramFamily",
        "Confidence",
        "EvidenceCount",
    ]
].rename(
    columns={
        "ProgramFamily": "InferredProgramFamily",
        "Confidence": "FamilyConfidence",
        "EvidenceCount": "FamilyEvidenceCount",
    }
)

subgroups_df = subgroups_df.merge(
    accepted_family,
    how="left",
    on="SubgroupCode",
    validate="one_to_one",
)

family_fill_mask = (
    subgroups_df["ProgramFamily"].isna()
    & subgroups_df["InferredProgramFamily"].notna()
)

subgroups_df.loc[
    family_fill_mask,
    "ProgramFamily",
] = subgroups_df.loc[
    family_fill_mask,
    "InferredProgramFamily",
]

subgroups_df.loc[
    family_fill_mask,
    "ProgramFamilySource",
] = "lecture_subgroup_cooccurrence"

# Bewaar inferencegegevens wanneer nog geen exacte inference bestond.
no_existing_confidence = (
    subgroups_df["InferenceConfidence"].isna()
)

subgroups_df.loc[
    family_fill_mask & no_existing_confidence,
    "InferenceConfidence",
] = subgroups_df.loc[
    family_fill_mask & no_existing_confidence,
    "FamilyConfidence",
]

subgroups_df.loc[
    family_fill_mask
    & subgroups_df["InferenceEvidenceCount"].isna(),
    "InferenceEvidenceCount",
] = subgroups_df.loc[
    family_fill_mask
    & subgroups_df["InferenceEvidenceCount"].isna(),
    "FamilyEvidenceCount",
]


# ============================================================
# CLEAN TEMPORARY COLUMNS
# ============================================================

subgroups_df = subgroups_df.drop(
    columns=[
        "InferredProgramName",
        "ExactConfidence",
        "ExactEvidenceCount",
        "InferredProgramFamily",
        "FamilyConfidence",
        "FamilyEvidenceCount",
    ],
    errors="ignore",
)


# ============================================================
# SAVE EVIDENCE
# ============================================================

exact_evidence_output = exact_counts.copy()
exact_evidence_output["InferenceType"] = "ExactProgramName"

family_evidence_output = family_counts.copy()
family_evidence_output = family_evidence_output.rename(
    columns={
        "ProgramFamily": "ProgramName",
    }
)
family_evidence_output["InferenceType"] = "ProgramFamily"

evidence_df = pd.concat(
    [
        exact_evidence_output,
        family_evidence_output,
    ],
    ignore_index=True,
    sort=False,
)

evidence_df.to_csv(
    EVIDENCE_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# SAVE OUTPUTS
# ============================================================

output_columns = [
    "SubgroupKey",
    "SubgroupCode",
    "ProgramName",
    "ProgramFamily",
    "ProgramNameSource",
    "ProgramFamilySource",
    "InferenceConfidence",
    "InferenceEvidenceCount",
]

subgroups_df = subgroups_df[output_columns]

subgroups_df.to_csv(
    OUTPUT_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

unresolved_df = subgroups_df[
    subgroups_df["ProgramName"].isna()
    & subgroups_df["ProgramFamily"].isna()
]

unresolved_df.to_csv(
    UNRESOLVED_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# SUMMARY
# ============================================================

known_from_students = (
    subgroups_df["ProgramNameSource"] == "students"
).sum()

exact_inferred = (
    subgroups_df["ProgramNameSource"]
    == "lecture_subgroup_cooccurrence"
).sum()

family_only_inferred = (
    subgroups_df["ProgramName"].isna()
    & subgroups_df["ProgramFamily"].notna()
).sum()

missing_exact = (
    subgroups_df["ProgramName"].isna()
).sum()

missing_everything = (
    subgroups_df["ProgramName"].isna()
    & subgroups_df["ProgramFamily"].isna()
).sum()

print("\n" + "=" * 75)
print("SUBGROUP COOCCURRENCE ENRICHMENT COMPLETE")
print("=" * 75)

print(
    f"Totaal aantal subgroepen:              "
    f"{len(subgroups_df):,}"
)

print(
    f"Exact bekend via students:             "
    f"{known_from_students:,}"
)

print(
    f"Exact afgeleid via lecturegroepen:     "
    f"{exact_inferred:,}"
)

print(
    f"Alleen ProgramFamily afgeleid:         "
    f"{family_only_inferred:,}"
)

print(
    f"Nog zonder exacte ProgramName:         "
    f"{missing_exact:,}"
)

print(
    f"Nog zonder ProgramName én family:      "
    f"{missing_everything:,}"
)

print("\nOutput:")
print(f"✅ {OUTPUT_CSV}")
print(f"📊 {EVIDENCE_CSV}")
print(f"❓ {UNRESOLVED_CSV}")