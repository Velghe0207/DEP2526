import ast
import os
import re

import pandas as pd


INPUT_FILE = (
    r"D:\Documents2\School\26-EP3\DEP\repo\DEP2-2025-2026-groep12"
    r"\data\cleaned\all_courses.csv"
)

OUTPUT_DIR = (
    r"D:\Documents2\School\26-EP3\DEP\repo\DEP2-2025-2026-groep12"
    r"\data\cleaned\SplitCourses"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize_text(value) -> str:
    """Maakt tekst geschikt voor betrouwbare vergelijkingen."""
    if pd.isna(value):
        return ""

    text = str(value).lower().strip()
    return re.sub(r"\s+", " ", text)


def extract_evaluation_formats(value) -> list[str]:
    """
    Haalt enkel de waarden van 'format' uit evaluation_methods.

    Het veld 'moment', zoals 'Binnen examenrooster',
    wordt dus niet gebruikt voor de classificatie.
    """
    if pd.isna(value):
        return []

    text = str(value)

    try:
        parsed_data = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        # Fallback wanneer het veld niet geldig geparsed kan worden
        matches = re.findall(
            r"""['"]format['"]\s*:\s*['"]([^'"]+)['"]""",
            text,
            flags=re.IGNORECASE,
        )

        return [normalize_text(match) for match in matches]

    formats = []

    def search(item):
        if isinstance(item, dict):
            for key, item_value in item.items():
                if normalize_text(key) == "format":
                    formats.append(normalize_text(item_value))
                else:
                    search(item_value)

        elif isinstance(item, (list, tuple)):
            for child in item:
                search(child)

    search(parsed_data)

    return formats


def classify_course(row) -> tuple[bool, str]:
    """
    Classificeert een vak als groepswerk of niet-groepswerk.

    Prioriteit:
    1. Schriftelijk/mondeling examen -> geen groepswerk
    2. 'project' in titel -> groepswerk
    3. Observatie functioneren student -> groepswerk
    4. Anders -> geen groepswerk
    """
    title = normalize_text(row["title"])
    formats = extract_evaluation_formats(row["evaluation_methods"])

    # Zeker geen groepswerk
    has_written_exam = any(
        "schriftelijk examen" in evaluation_format
        for evaluation_format in formats
    )

    has_oral_exam = any(
        "mondeling examen" in evaluation_format
        for evaluation_format in formats
    )

    if has_written_exam:
        return False, "Schriftelijk examen"

    if has_oral_exam:
        return False, "Mondeling examen"

    # Zeker wel een groepswerk
    if re.search(r"\bproject\b", title, flags=re.IGNORECASE):
        return True, "Project in titel"

    has_student_observation = any(
        "observatie van functioneren van de student" in evaluation_format
        for evaluation_format in formats
    )

    if has_student_observation:
        return True, "Observatie van functioneren van de student"

    # Geen sterk bewijs dat het een verplicht groepswerk is
    return False, "Geen sterk signaal voor verplicht groepswerk"


# CSV inlezen
df = pd.read_csv(INPUT_FILE)

required_columns = {"title", "evaluation_methods"}
missing_columns = required_columns - set(df.columns)

if missing_columns:
    raise ValueError(
        "Ontbrekende kolommen: "
        + ", ".join(sorted(missing_columns))
    )


# Classificatie uitvoeren
results = df.apply(classify_course, axis=1)

df["is_group_project"] = results.apply(lambda result: result[0])
df["classification_reason"] = results.apply(lambda result: result[1])


# Opsplitsen
group_projects = df[df["is_group_project"]].copy()
non_group_projects = df[~df["is_group_project"]].copy()


# Bestanden schrijven
group_projects.to_csv(
    os.path.join(OUTPUT_DIR, "group_projects.csv"),
    index=False,
    encoding="utf-8-sig",
)

non_group_projects.to_csv(
    os.path.join(OUTPUT_DIR, "non_group_projects.csv"),
    index=False,
    encoding="utf-8-sig",
)


# Controlebestand met de gebruikte evaluatieformats
review_df = df.copy()

review_df["parsed_evaluation_formats"] = review_df[
    "evaluation_methods"
].apply(
    lambda value: " | ".join(extract_evaluation_formats(value))
)

review_df.to_csv(
    os.path.join(OUTPUT_DIR, "course_classification_review.csv"),
    index=False,
    encoding="utf-8-sig",
)


# Resultaten tonen
print(f"Totaal aantal vakken: {len(df)}")
print(f"Groepswerken: {len(group_projects)}")
print(f"Niet-groepswerken: {len(non_group_projects)}")

print("\nGevonden groepswerken:")

if group_projects.empty:
    print("Geen groepswerken gevonden.")
else:
    print(
        group_projects[
            ["title", "classification_reason"]
        ]
        .sort_values("title")
        .to_string(index=False)
    )

print(f"\nBestanden opgeslagen in:\n{OUTPUT_DIR}")