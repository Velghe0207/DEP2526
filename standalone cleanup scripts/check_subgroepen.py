from pathlib import Path
import csv

import pandas as pd


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"D:\Documents2\School\26-EP3\DEP\repo"
    r"\DEP2-2025-2026-groep12\00 data"
)

# Bestand met de betrouwbare SUBGROEPID → SUBGROEPCODE-mapping
REFERENCE_CSV = (
    BASE_DIR
    / "cleaned"
    / "unique_subgroups.csv"
)

# Het bestand dat we daarnet genereerden
GENERATED_CSV = (
    BASE_DIR
    / "raw"
    / "subgroups"
    / "all_subgroups_enriched.csv"
)

# Vergelijkingsresultaten
OUTPUT_DIR = (
    BASE_DIR
    / "raw"
    / "subgroups"
    / "comparison"
)

MATCHES_CSV = OUTPUT_DIR / "subgroup_program_matches.csv"
CONFLICTS_CSV = OUTPUT_DIR / "subgroup_program_conflicts.csv"
CAN_FILL_CSV = OUTPUT_DIR / "subgroups_programname_can_be_filled.csv"
ONLY_REFERENCE_CSV = OUTPUT_DIR / "subgroups_only_in_reference.csv"
ONLY_GENERATED_CSV = OUTPUT_DIR / "subgroups_only_in_generated.csv"

# Optioneel: genereer meteen een verbeterde versie
UPDATED_OUTPUT_CSV = (
    BASE_DIR
    / "raw"
    / "subgroups"
    / "all_subgroups_enriched_updated.csv"
)

# True = ontbrekende ProgramNames automatisch invullen
# False = alleen vergelijken
FILL_MISSING_PROGRAMNAMES = True

# True = bestaande conflicterende ProgramNames overschrijven met
# de waarde uit cleaned/unique_subgroups.csv
#
# Voorlopig best False laten en conflicten eerst bekijken.
OVERWRITE_CONFLICTS = False


# ============================================================
# 2. HELPERS
# ============================================================

def detect_separator(file_path: Path) -> str:
    """Detecteer komma, puntkomma of tab als separator."""
    with file_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:
        sample = file.read(8192)

    try:
        return csv.Sniffer().sniff(
            sample,
            delimiters=";,\t",
        ).delimiter
    except csv.Error:
        return ","


def read_csv_auto(file_path: Path) -> pd.DataFrame:
    """Lees een CSV-bestand met automatische separatordetectie."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Bestand niet gevonden:\n{file_path}"
        )

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
        f"✅ Gelezen: {file_path.name}"
        f" | rijen: {len(df):,}"
        f" | separator: {repr(separator)}"
    )
    print(f"   Kolommen: {list(df.columns)}")

    return df


def normalize_identifier(series: pd.Series) -> pd.Series:
    """
    Normaliseer subgroep-ID's.

    Zo worden bijvoorbeeld:
    5717692
    5717692.0
    ' 5717692 '
    allemaal '5717692'.
    """
    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )


def normalize_program_name(series: pd.Series) -> pd.Series:
    """Verwijder overbodige spaties en normaliseer lege waarden."""
    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace(
            {
                "": pd.NA,
                "nan": pd.NA,
                "None": pd.NA,
                "<NA>": pd.NA,
            }
        )
    )


def normalized_comparison_value(series: pd.Series) -> pd.Series:
    """
    Maak een tijdelijke vergelijkingswaarde.

    Hoofdletterverschillen en extra spaties worden genegeerd.
    """
    return (
        normalize_program_name(series)
        .str.upper()
    )


# ============================================================
# 3. LOAD REFERENCE FILE
# ============================================================

reference_df = read_csv_auto(REFERENCE_CSV)

required_reference_columns = [
    "SUBGROEPID",
    "SUBGROEPCODE",
]

missing_reference_columns = [
    column
    for column in required_reference_columns
    if column not in reference_df.columns
]

if missing_reference_columns:
    raise KeyError(
        "Ontbrekende kolommen in unique_subgroups.csv:\n"
        + "\n".join(
            f"- {column}"
            for column in missing_reference_columns
        )
    )

reference_df = reference_df[
    [
        "SUBGROEPID",
        "SUBGROEPCODE",
    ]
].copy()

reference_df = reference_df.rename(
    columns={
        "SUBGROEPID": "SubgroupCode",
        "SUBGROEPCODE": "ReferenceProgramName",
    }
)

reference_df["SubgroupCode"] = normalize_identifier(
    reference_df["SubgroupCode"]
)

reference_df["ReferenceProgramName"] = normalize_program_name(
    reference_df["ReferenceProgramName"]
)

reference_df = reference_df.dropna(
    subset=[
        "SubgroupCode",
        "ReferenceProgramName",
    ]
)


# ============================================================
# 4. CHECK REFERENCE DUPLICATES AND CONFLICTS
# ============================================================

reference_program_counts = (
    reference_df
    .groupby("SubgroupCode")["ReferenceProgramName"]
    .nunique()
)

conflicting_reference_codes = reference_program_counts[
    reference_program_counts > 1
].index

if len(conflicting_reference_codes) > 0:
    reference_conflicts = (
        reference_df[
            reference_df["SubgroupCode"].isin(
                conflicting_reference_codes
            )
        ]
        .drop_duplicates()
        .sort_values(
            [
                "SubgroupCode",
                "ReferenceProgramName",
            ]
        )
    )

    conflict_path = (
        OUTPUT_DIR
        / "conflicts_inside_reference_file.csv"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    reference_conflicts.to_csv(
        conflict_path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n⚠️ Het referentiebestand bevat SUBGROEPID's "
        "met meerdere SUBGROEPCODE-waarden."
    )
    print(f"Conflicten: {len(conflicting_reference_codes):,}")
    print(f"Opgeslagen in:\n{conflict_path}")

    raise ValueError(
        "Los eerst de interne conflicten in unique_subgroups.csv op."
    )

reference_df = (
    reference_df
    .drop_duplicates(
        subset=["SubgroupCode"],
        keep="first",
    )
    .reset_index(drop=True)
)

print(
    f"\nUnieke subgroepen in referentiebestand: "
    f"{len(reference_df):,}"
)


# ============================================================
# 5. LOAD GENERATED FILE
# ============================================================

generated_df = read_csv_auto(GENERATED_CSV)

required_generated_columns = [
    "SubgroupCode",
    "ProgramName",
]

missing_generated_columns = [
    column
    for column in required_generated_columns
    if column not in generated_df.columns
]

if missing_generated_columns:
    raise KeyError(
        "Ontbrekende kolommen in het gegenereerde bestand:\n"
        + "\n".join(
            f"- {column}"
            for column in missing_generated_columns
        )
    )

generated_df["SubgroupCode"] = normalize_identifier(
    generated_df["SubgroupCode"]
)

generated_df["ProgramName"] = normalize_program_name(
    generated_df["ProgramName"]
)

duplicate_generated_codes = (
    generated_df["SubgroupCode"]
    .duplicated(keep=False)
)

if duplicate_generated_codes.any():
    duplicate_rows = (
        generated_df[
            duplicate_generated_codes
        ]
        .sort_values("SubgroupCode")
    )

    duplicate_path = (
        OUTPUT_DIR
        / "duplicate_subgroupcodes_in_generated.csv"
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    duplicate_rows.to_csv(
        duplicate_path,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    raise ValueError(
        "Het gegenereerde bestand bevat dubbele SubgroupCodes.\n"
        f"Controlebestand:\n{duplicate_path}"
    )


# ============================================================
# 6. COMPARE BOTH FILES
# ============================================================

comparison_df = generated_df.merge(
    reference_df,
    how="outer",
    on="SubgroupCode",
    indicator=True,
    validate="one_to_one",
)

comparison_df["GeneratedComparisonValue"] = (
    normalized_comparison_value(
        comparison_df["ProgramName"]
    )
)

comparison_df["ReferenceComparisonValue"] = (
    normalized_comparison_value(
        comparison_df["ReferenceProgramName"]
    )
)

in_both_mask = comparison_df["_merge"].eq("both")

match_mask = (
    in_both_mask
    & comparison_df["ProgramName"].notna()
    & comparison_df["ReferenceProgramName"].notna()
    & (
        comparison_df["GeneratedComparisonValue"]
        == comparison_df["ReferenceComparisonValue"]
    )
)

can_fill_mask = (
    in_both_mask
    & comparison_df["ProgramName"].isna()
    & comparison_df["ReferenceProgramName"].notna()
)

conflict_mask = (
    in_both_mask
    & comparison_df["ProgramName"].notna()
    & comparison_df["ReferenceProgramName"].notna()
    & (
        comparison_df["GeneratedComparisonValue"]
        != comparison_df["ReferenceComparisonValue"]
    )
)

only_reference_mask = comparison_df["_merge"].eq(
    "right_only"
)

only_generated_mask = comparison_df["_merge"].eq(
    "left_only"
)


# ============================================================
# 7. SAVE COMPARISON RESULTS
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

comparison_output_columns = [
    column
    for column in [
        "SubgroupKey",
        "SubgroupCode",
        "ProgramName",
        "ReferenceProgramName",
        "ProgramFamily",
        "ProgramNameSource",
        "ProgramFamilySource",
        "InferenceConfidence",
        "InferenceEvidenceCount",
    ]
    if column in comparison_df.columns
]

comparison_df.loc[
    match_mask,
    comparison_output_columns,
].to_csv(
    MATCHES_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

comparison_df.loc[
    can_fill_mask,
    comparison_output_columns,
].to_csv(
    CAN_FILL_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

comparison_df.loc[
    conflict_mask,
    comparison_output_columns,
].to_csv(
    CONFLICTS_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

comparison_df.loc[
    only_reference_mask,
    comparison_output_columns,
].to_csv(
    ONLY_REFERENCE_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)

comparison_df.loc[
    only_generated_mask,
    comparison_output_columns,
].to_csv(
    ONLY_GENERATED_CSV,
    sep=";",
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 8. OPTIONALLY FILL MISSING PROGRAMNAMES
# ============================================================

if FILL_MISSING_PROGRAMNAMES:
    updated_df = generated_df.merge(
        reference_df,
        how="left",
        on="SubgroupCode",
        validate="one_to_one",
    )

    # Zet numerieke metadata opnieuw om naar numerieke types.
    # read_csv_auto leest standaard alles als string in.
    if "ProgramNameConfidence" in updated_df.columns:
        updated_df["ProgramNameConfidence"] = pd.to_numeric(
            updated_df["ProgramNameConfidence"],
            errors="coerce",
        )

    if "InferenceConfidence" in updated_df.columns:
        updated_df["InferenceConfidence"] = pd.to_numeric(
            updated_df["InferenceConfidence"],
            errors="coerce",
        )

    if "InferenceEvidenceCount" in updated_df.columns:
        updated_df["InferenceEvidenceCount"] = pd.to_numeric(
            updated_df["InferenceEvidenceCount"],
            errors="coerce",
        ).astype("Int64")

    missing_before = updated_df["ProgramName"].isna()

    fill_mask = (
        missing_before
        & updated_df["ReferenceProgramName"].notna()
    )

    updated_df.loc[
        fill_mask,
        "ProgramName",
    ] = updated_df.loc[
        fill_mask,
        "ReferenceProgramName",
    ]

    if "ProgramNameSource" not in updated_df.columns:
        updated_df["ProgramNameSource"] = pd.NA

    updated_df.loc[
        fill_mask,
        "ProgramNameSource",
    ] = "cleaned_unique_subgroups"

    if "ProgramNameConfidence" in updated_df.columns:
        updated_df.loc[
            fill_mask,
            "ProgramNameConfidence",
        ] = 1.0

    if "InferenceConfidence" in updated_df.columns:
        updated_df.loc[
            fill_mask,
            "InferenceConfidence",
        ] = 1.0

    # Een directe mapping uit unique_subgroups.csv is geen inferentie
    # op basis van meerdere lectures. Daarom kan EvidenceCount leeg blijven.
    if "InferenceEvidenceCount" in updated_df.columns:
        updated_df.loc[
            fill_mask,
            "InferenceEvidenceCount",
        ] = pd.NA

    if OVERWRITE_CONFLICTS:
        generated_compare = normalized_comparison_value(
            updated_df["ProgramName"]
        )

        reference_compare = normalized_comparison_value(
            updated_df["ReferenceProgramName"]
        )

        overwrite_mask = (
            updated_df["ProgramName"].notna()
            & updated_df["ReferenceProgramName"].notna()
            & generated_compare.ne(reference_compare)
        )

        updated_df.loc[
            overwrite_mask,
            "ProgramName",
        ] = updated_df.loc[
            overwrite_mask,
            "ReferenceProgramName",
        ]

        updated_df.loc[
            overwrite_mask,
            "ProgramNameSource",
        ] = "cleaned_unique_subgroups_override"

        if "InferenceConfidence" in updated_df.columns:
            updated_df.loc[
                overwrite_mask,
                "InferenceConfidence",
            ] = 1.0

        print(
            f"\nBestaande conflicten overschreven: "
            f"{overwrite_mask.sum():,}"
        )

    updated_df = updated_df.drop(
        columns=["ReferenceProgramName"],
        errors="ignore",
    )

    updated_df.to_csv(
        UPDATED_OUTPUT_CSV,
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )


# ============================================================
# 9. PRINT SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("SUBGROUP COMPARISON COMPLETE")
print("=" * 75)

print(
    f"Subgroepen in gegenereerd bestand: "
    f"{len(generated_df):,}"
)

print(
    f"Subgroepen in referentiebestand:   "
    f"{len(reference_df):,}"
)

print(
    f"Subgroepen aanwezig in beide:      "
    f"{in_both_mask.sum():,}"
)

print(
    f"Bestaande ProgramNames gelijk:     "
    f"{match_mask.sum():,}"
)

print(
    f"Ontbrekend maar direct invulbaar:  "
    f"{can_fill_mask.sum():,}"
)

print(
    f"Conflicterende ProgramNames:       "
    f"{conflict_mask.sum():,}"
)

print(
    f"Alleen in referentiebestand:       "
    f"{only_reference_mask.sum():,}"
)

print(
    f"Alleen in gegenereerd bestand:     "
    f"{only_generated_mask.sum():,}"
)

missing_before_count = (
    generated_df["ProgramName"].isna().sum()
)

expected_missing_after = (
    missing_before_count
    - can_fill_mask.sum()
)

print("\n=== VERWACHTE VERBETERING ===")
print(
    f"Ontbrekende ProgramNames vóór:     "
    f"{missing_before_count:,}"
)

print(
    f"Direct aan te vullen:              "
    f"{can_fill_mask.sum():,}"
)

print(
    f"Ontbrekend na aanvulling:          "
    f"{expected_missing_after:,}"
)

if len(generated_df) > 0:
    coverage_before = (
        generated_df["ProgramName"].notna().mean()
        * 100
    )

    coverage_after = (
        (
            len(generated_df)
            - expected_missing_after
        )
        / len(generated_df)
        * 100
    )

    print(
        f"Dekking vóór:                      "
        f"{coverage_before:.2f}%"
    )

    print(
        f"Verwachte dekking na aanvulling:   "
        f"{coverage_after:.2f}%"
    )

print("\nControlebestanden:")
print(f"✅ Matches:\n   {MATCHES_CSV}")
print(f"➕ Direct invulbaar:\n   {CAN_FILL_CSV}")
print(f"⚠️ Conflicten:\n   {CONFLICTS_CSV}")
print(f"➡️ Alleen in referentie:\n   {ONLY_REFERENCE_CSV}")
print(f"⬅️ Alleen in gegenereerd:\n   {ONLY_GENERATED_CSV}")

if FILL_MISSING_PROGRAMNAMES:
    print(
        f"\n💾 Verbeterd bestand:\n"
        f"   {UPDATED_OUTPUT_CSV}"
    )