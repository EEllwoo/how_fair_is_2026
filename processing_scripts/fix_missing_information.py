"""
This file finds and fixes any errors involving artefact DOIs in our results.
"""

import csv
import re
from typing import List, Tuple, Set

# Normalises a piece of text (lowercases and removes extra spaces)
def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text

# Finds and fixes incorrect information for a CSV using a reference list of paper titles and their artefact DOIs
def find_and_fix_missing_papers(
    tsv_path: str,
    csv_path: str,
    output_csv_path: str = None,
) -> List[int]:
    """Identify missing papers and fix DOIs using title-match mapping.

    Returns list of row indices in csv where DOI was corrected.

    - tsv_path: paper_titles.tsv (Title + DOI)
    - csv_path: FAIR results csv that contains DOI (of paper) and Paper Name:
    - output_csv_path: if provided, write corrected CSV here (else in-place overwrite csv_path).
    """

    # Load the list of papers and retrieve the artefact DOI for each
    title_to_doi = {}
    with open(tsv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            title = normalize_text(row.get("Title", ""))
            doi = (row.get("DOI") or "").strip()
            if title and doi:
                title_to_doi[title] = doi

    corrected_rows = []

    # Read the CSV file
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        csv_fieldnames = reader.fieldnames or []
        rows = list(reader)

    # Find and apply corrections to the CSV
    for i, row in enumerate(rows, start=2):  # Includes the header as the first row
        doi_key = "DOI (of paper)" if "DOI (of paper)" in row else "DOI" if "DOI" in row else "doi"
        existing_doi = (row.get(doi_key) or "").strip()
        paper_name = normalize_text(row.get("Paper Name:") or row.get("Paper Name") or row.get("Title") or "")

        if not existing_doi and paper_name:
            # If we are missing an artefact DOI in the result row but we have the title, find the DOI from the reference list and use it
            if paper_name in title_to_doi:
                row[doi_key] = title_to_doi[paper_name]
                corrected_rows.append(i)
            continue

        if existing_doi and existing_doi not in title_to_doi.values() and paper_name in title_to_doi:
            # If the existing DOI seems erroneous, replace it with the trusted one from paper_titles (our reference list)
            row[doi_key] = title_to_doi[paper_name]
            corrected_rows.append(i)

    # Write the corrected table to our output CSV
    write_path = output_csv_path or csv_path
    with open(write_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return corrected_rows

# Runs the script on our second pass results
if __name__ == "__main__":
    fixed = find_and_fix_missing_papers(
        tsv_path="paper_titles.tsv",
        csv_path="results/second.csv",
        output_csv_path="results/second_fixed.csv"
    )
    print(f"Corrected {len(fixed)} rows: {fixed}")
