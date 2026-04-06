import requests
import json

# Session cookies from your browser
COOKIES = {
"ezproxy": "WJsBVhagUtvemKft3ZynupdAAtMf6KF",
    "ezproxyl": "WJsBVhagUtvemKft3ZynupdAAtMf6KF",
    "ezproxyn": "WJsBVhagUtvemKft3ZynupdAAtMf6KF",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://ieeexplore-ieee-org.sheffield.idm.oclc.org/xpl/conhome/11029684/proceeding",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

BASE = "https://ieeexplore-ieee-org.sheffield.idm.oclc.org"

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)


def fetch_titles(isnumber="11029718", rows_per_page=100):
    all_papers = []
    page = 1

    while True:
        print(f"Fetching page {page}...")

        api_url = f"{BASE}/rest/search"
        payload = {
            "newsearch": True,
            "isnumber": isnumber,
            "sortType": "vol-only-seq",
            "rowsPerPage": rows_per_page,
            "pageNumber": page,
        }

        resp = session.post(api_url, json=payload)
        print(f"  Status: {resp.status_code}")

        if resp.status_code != 200:
            print(f"  Error: {resp.text[:500]}")
            break

        try:
            data = resp.json()
        except json.JSONDecodeError:
            print("  Failed to parse JSON. Response preview:")
            print(resp.text[:1000])
            break

        records = data.get("records", [])
        if not records:
            print("  No more records found.")
            break

        for article in records:
            title = article.get("articleTitle", "").strip()
            doi = article.get("doi", "").strip()
            if title:
                all_papers.append({"title": title, "doi": doi})

        total = data.get("totalRecords", 0)
        print(f"  Got {len(records)} records (total: {total})")

        if len(all_papers) >= total:
            break

        page += 1

    return all_papers


if __name__ == "__main__":
    papers = fetch_titles()

    print(f"\n{'='*60}")
    print(f"Total papers found: {len(papers)}")
    print('='*60)
    for i, p in enumerate(papers, 1):
        print(f"{i:4}. {p['title']}")
        if p['doi']:
            print(f"      DOI: {p['doi']}")

    # Save to TSV file with title and DOI columns
    output_file = "paper_titles.tsv"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("INDEX\tTitle\tDOI\n")
        for i, paper in enumerate(papers, 1):
            f.write(f"{i}\t{paper['title']}\t{paper['doi']}\n")
    
    print(f"\nSaved to {output_file}")