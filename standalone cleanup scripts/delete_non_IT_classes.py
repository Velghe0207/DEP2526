import csv
import sys
from pathlib import Path

import pyodbc


# ---------------------------------------------------------------------
# BESTANDSPADEN
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(
    r"D:\Documents2\School\26-EP3\DEP\repo"
    r"\DEP2-2025-2026-groep12"
)

INPUT_CSV_PATH = (
    PROJECT_ROOT
    / "00 data"
    / "raw"
    / "courses"
    / "all_courses.csv"
)

OUTPUT_CSV_PATH = (
    PROJECT_ROOT
    / "00 data"
    / "cleaned"
    / "all_IT_courses.csv"
)


# ---------------------------------------------------------------------
# SQL SERVER
# ---------------------------------------------------------------------

SERVER = r"localhost\MSSQLSERVER2019"
DATABASE = "DEP2"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)


# ---------------------------------------------------------------------
# FILTERLOGICA
# ---------------------------------------------------------------------

def is_it_course(faculties: str | None) -> bool:
    """
    Bepaal of een vak tot IT behoort.

    Geldige voorbeelden:
    - ['Bachelor in de toegepaste informatica, trajectschijf 1']
    - ['IC IT, trajectschijf 2']
    """
    if faculties is None:
        return False

    normalized_faculties = faculties.strip().casefold()

    return (
        "toegepaste informatica" in normalized_faculties
        or "ic it" in normalized_faculties
    )


def normalize_class_code(code: str | None) -> str | None:
    """Maak een classcode vergelijkbaar met DimClass.ClassCode."""
    if code is None:
        return None

    normalized_code = code.strip()

    if not normalized_code:
        return None

    return normalized_code


# ---------------------------------------------------------------------
# CSV FILTEREN
# ---------------------------------------------------------------------

def create_it_courses_csv(
    input_path: Path,
    output_path: Path,
) -> set[str]:
    """
    Filter alle IT-vakken uit het ruwe CSV-bestand.

    Het gefilterde bestand wordt opgeslagen als all_IT_courses.csv.
    De functie geeft alle unieke IT-classcodes terug.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Het invoerbestand bestaat niet:\n{input_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    it_rows: list[dict[str, str]] = []
    class_codes: set[str] = set()

    with input_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as input_file:
        reader = csv.DictReader(input_file)

        if not reader.fieldnames:
            raise ValueError(
                "Het CSV-bestand bevat geen kolomnamen."
            )

        required_columns = {"faculties", "code"}
        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise ValueError(
                "De volgende verplichte kolommen ontbreken: "
                f"{sorted(missing_columns)}.\n"
                f"Gevonden kolommen: {reader.fieldnames}"
            )

        for row in reader:
            if not is_it_course(row.get("faculties")):
                continue

            it_rows.append(row)

            class_code = normalize_class_code(row.get("code"))

            if class_code:
                class_codes.add(class_code)

    if not it_rows:
        raise RuntimeError(
            "Er werden geen IT-vakken gevonden. "
            "Het uitvoerbestand en de database worden niet aangepast."
        )

    if not class_codes:
        raise RuntimeError(
            "Er werden IT-vakken gevonden, maar geen geldige classcodes. "
            "De database wordt niet aangepast."
        )

    with output_path.open(
        mode="w",
        encoding="utf-8-sig",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=reader.fieldnames,
        )

        writer.writeheader()
        writer.writerows(it_rows)

    print("CSV-filtering voltooid.")
    print(f"Ruw invoerbestand: {input_path}")
    print(f"Gefilterd bestand: {output_path}")
    print(f"IT-vakken overgehouden: {len(it_rows):,}")
    print(f"Unieke IT-classcodes: {len(class_codes):,}")

    return class_codes


# ---------------------------------------------------------------------
# TERMINALUITVOER PROBLEEMRIJEN
# ---------------------------------------------------------------------

def print_problem_factlectures(
    cursor: pyodbc.Cursor,
) -> None:
    """Toon FactLecture-rijen die niet aan een geldige IT-class gekoppeld zijn."""
    cursor.execute("""
        SELECT
            FL.LectureID,
            FL.ClassKey,
            C.ClassCode,
            C.ClassName,
            FL.SubgroupKey
        FROM dbo.FactLecture AS FL
        INNER JOIN dbo.DimClass AS C
            ON C.ClassKey = FL.ClassKey
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM #InformaticaClassCodes AS I
            WHERE I.ClassCode =
                LTRIM(
                    RTRIM(
                        CONVERT(NVARCHAR(255), C.ClassCode)
                    )
                )
        )
        ORDER BY
            C.ClassCode,
            FL.LectureID;
    """)

    problem_rows = cursor.fetchall()

    print(
        f"{'LectureID':<15}"
        f"{'ClassKey':<12}"
        f"{'ClassCode':<20}"
        f"{'SubgroupKey':<15}"
        f"{'ClassName'}"
    )
    print("-" * 110)

    for row in problem_rows:
        print(
            f"{str(row.LectureID):<15}"
            f"{str(row.ClassKey):<12}"
            f"{str(row.ClassCode):<20}"
            f"{str(row.SubgroupKey):<15}"
            f"{str(row.ClassName)}"
        )


def print_problem_class_summary(
    cursor: pyodbc.Cursor,
) -> None:
    """Toon een compact overzicht per classcode."""
    cursor.execute("""
        SELECT
            C.ClassKey,
            C.ClassCode,
            C.ClassName,
            COUNT(*) AS LectureCount
        FROM dbo.FactLecture AS FL
        INNER JOIN dbo.DimClass AS C
            ON C.ClassKey = FL.ClassKey
        WHERE NOT EXISTS
        (
            SELECT 1
            FROM #InformaticaClassCodes AS I
            WHERE I.ClassCode =
                LTRIM(
                    RTRIM(
                        CONVERT(NVARCHAR(255), C.ClassCode)
                    )
                )
        )
        GROUP BY
            C.ClassKey,
            C.ClassCode,
            C.ClassName
        ORDER BY
            LectureCount DESC,
            C.ClassCode;
    """)

    rows = cursor.fetchall()

    print("\nSamenvatting per problematische class:\n")

    print(
        f"{'ClassKey':<12}"
        f"{'ClassCode':<20}"
        f"{'Lectures':<12}"
        f"{'ClassName'}"
    )
    print("-" * 90)

    for row in rows:
        print(
            f"{str(row.ClassKey):<12}"
            f"{str(row.ClassCode):<20}"
            f"{str(row.LectureCount):<12}"
            f"{str(row.ClassName)}"
        )


# ---------------------------------------------------------------------
# DATABASE OPSCHONEN
# ---------------------------------------------------------------------

def delete_non_it_classes(class_codes: set[str]) -> None:
    """
    Verwijder alle classes uit DimClass waarvan ClassCode niet voorkomt
    in het gefilterde all_IT_courses.csv-bestand.
    """
    connection = pyodbc.connect(CONNECTION_STRING)
    connection.autocommit = False

    try:
        cursor = connection.cursor()

        # Tijdelijke tabel met de toegelaten IT-classcodes.
        cursor.execute("""
            CREATE TABLE #InformaticaClassCodes
            (
                ClassCode NVARCHAR(255) NOT NULL PRIMARY KEY
            );
        """)

        cursor.fast_executemany = True

        cursor.executemany(
            """
            INSERT INTO #InformaticaClassCodes (ClassCode)
            VALUES (?);
            """,
            [(code,) for code in sorted(class_codes)],
        )

        # -------------------------------------------------------------
        # CONTROLE DIMCLASS
        # -------------------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.DimClass AS C
            WHERE EXISTS
            (
                SELECT 1
                FROM #InformaticaClassCodes AS I
                WHERE I.ClassCode =
                    LTRIM(
                        RTRIM(
                            CONVERT(NVARCHAR(255), C.ClassCode)
                        )
                    )
            );
        """)

        classes_to_keep = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.DimClass AS C
            WHERE NOT EXISTS
            (
                SELECT 1
                FROM #InformaticaClassCodes AS I
                WHERE I.ClassCode =
                    LTRIM(
                        RTRIM(
                            CONVERT(NVARCHAR(255), C.ClassCode)
                        )
                    )
            );
        """)

        classes_to_delete = cursor.fetchone()[0]

        print("\nControle DimClass:")
        print(f"Classes die behouden worden: {classes_to_keep:,}")
        print(f"Classes die verwijderd zouden worden: {classes_to_delete:,}")

        # -------------------------------------------------------------
        # VEILIGHEIDSCONTROLE FACTLECTURE
        # -------------------------------------------------------------

        cursor.execute("""
            SELECT COUNT(*)
            FROM dbo.FactLecture AS FL
            INNER JOIN dbo.DimClass AS C
                ON C.ClassKey = FL.ClassKey
            WHERE NOT EXISTS
            (
                SELECT 1
                FROM #InformaticaClassCodes AS I
                WHERE I.ClassCode =
                    LTRIM(
                        RTRIM(
                            CONVERT(NVARCHAR(255), C.ClassCode)
                        )
                    )
            );
        """)

        invalid_factlecture_rows = cursor.fetchone()[0]

        if invalid_factlecture_rows > 0:
            print(
                "\nVerwijderen geannuleerd."
            )
            print(
                f"Er zijn nog {invalid_factlecture_rows:,} "
                "FactLecture-rijen gekoppeld aan classes waarvan de "
                "ClassCode niet in all_IT_courses.csv staat.\n"
            )

            print_problem_class_summary(cursor)

            print("\nAlle problematische FactLecture-rijen:\n")
            print_problem_factlectures(cursor)

            connection.rollback()

            print(
                "\nEr is niets uit DimClass verwijderd."
            )
            print(
                "Controleer eerst of deze classes werkelijk niet tot IT behoren."
            )

            return

        # -------------------------------------------------------------
        # DIMCLASS OPSCHONEN
        # -------------------------------------------------------------

        cursor.execute("""
            DELETE C
            FROM dbo.DimClass AS C
            WHERE NOT EXISTS
            (
                SELECT 1
                FROM #InformaticaClassCodes AS I
                WHERE I.ClassCode =
                    LTRIM(
                        RTRIM(
                            CONVERT(NVARCHAR(255), C.ClassCode)
                        )
                    )
            );
        """)

        deleted_rows = cursor.rowcount

        connection.commit()

        print(
            f"\nKlaar: {deleted_rows:,} niet-IT-classes "
            "uit DimClass verwijderd."
        )

    except Exception:
        connection.rollback()

        print(
            "\nEr is een fout opgetreden. "
            "Alle databasewijzigingen zijn teruggedraaid."
        )

        raise

    finally:
        connection.close()


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    try:
        class_codes = create_it_courses_csv(
            input_path=INPUT_CSV_PATH,
            output_path=OUTPUT_CSV_PATH,
        )

        delete_non_it_classes(class_codes)

    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"\nFout: {error}")
        sys.exit(1)

    except pyodbc.Error as error:
        print("\nSQL Server-fout:")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()