import csv

PAPER_TSV = "results/paper_titles.tsv"
RESULT_CSV = "results/first_doi_fixed.csv"


def load_paper_dois(path):
    papers = []
    with open(path, encoding="utf-8", newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for idx, row in enumerate(reader, start=1):
            doi = (row.get("DOI") or row.get("doi") or "").strip()
            title = row.get("Title", "").strip()
            papers.append((idx, title, doi))
    return papers


import re

def normalize_text(text):
    if text is None:
        return ""
    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def load_result_dois(path):
    dois = set()
    with open(path, encoding="utf-8", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doi = (row.get("DOI (of paper)") or row.get("DOI") or row.get("doi") or "").strip()
            if doi:
                dois.add(doi)
    return dois


def load_result_titles(path):
    titles = set()
    with open(path, encoding="utf-8", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            paper_name = row.get("Paper Name:") or row.get("Paper Name") or row.get("Title") or ""
            titles.add(normalize_text(paper_name))
    return titles


def doi_report(result_csv=RESULT_CSV, paper_tsv=PAPER_TSV):
    papers = load_paper_dois(paper_tsv)
    result_dois = load_result_dois(result_csv)
    result_titles = load_result_titles(result_csv)


    missing = []
    found_by_title = []
    missing_no_doi = []

    for idx, title, doi in papers:


        normalized_title = normalize_text(title)

        if not doi:
            missing_no_doi.append((idx, title))
            continue

        if doi in result_dois:
            continue

        if normalized_title and normalized_title in result_titles:
            found_by_title.append((idx, title, doi))
            continue

        missing.append((idx, title, doi))


    # if missing:
    #     print("Missing DOI rows from paper_titles.tsv (no DOI and no title match):")
    #      for idx, title, doi in missing:
    #          print(f"{idx}:({title})")

    # if found_by_title:
    #     print("\nRows where DOI was missing but title matched in results:")
    #     for idx, title, doi in found_by_title:
    #         print(f"{idx}: {doi} ({title})")

    # if missing_no_doi:
    #     print("\npaper_titles rows with an empty DOI:")
    #     for idx, title in missing_no_doi:
    #         print(f"{idx}: {title}")
            
    print(f"Paper titles: {len(papers)}")
    print(f"Result DOIs: {len(result_dois)}")
    print(f"Result paper names: {len(result_titles)}")
    print(f"Missing by DOI and title: {len(missing)}")
    print(f"Paper entries with missing DOI field: {len(missing_no_doi)}\n")
    print(f"Matched by title fallback: {len(found_by_title)}")


