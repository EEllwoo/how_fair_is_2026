from pathlib import Path

import pandas as pd

from plotting.FAIR_compliance import FAIR_CRITERIA
from pre_reports.missing_papers import normalize_text
from pre_reports.pre_process import scleaned_pandas


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIRST_PASS = PROJECT_ROOT / "results" / "FAIR Evaluation Results - First Pass Responses_fixed.csv"
DEFAULT_SECOND_PASS = PROJECT_ROOT / "results" / "FAIR Evaluation Results - Second Pass Responses_fixed.csv"

PAPER_NAME_COLUMN = "Paper Name:"
DOI_COLUMN = "DOI (of paper)"
PASS_LABELS = ("First Pass", "Second Pass")
EXCLUDED_ALL_FIELDS = {PAPER_NAME_COLUMN, "Timestamp", "Reviewer Name"}
FAIR_FIELDS = [criterion for criteria in FAIR_CRITERIA.values() for criterion in criteria]
FAIR_LETTER_BY_FIELD = {
    criterion: letter
    for letter, criteria in FAIR_CRITERIA.items()
    for criterion in criteria
}
ROW_KEY_COLUMN = "__row_key"
DISPLAY_NAME_COLUMN = "__display_name"


def _normalize_scalar(value):
    if isinstance(value, pd.Series):
        for item in value.tolist():
            normalized_item = _normalize_scalar(item)
            if normalized_item:
                return normalized_item
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip().replace("–", "-")


def _normalize_title(value):
    return normalize_text(_normalize_scalar(value))


def _normalize_doi(value):
    doi = _normalize_scalar(value).lower()
    if doi.startswith("https://doi.org/"):
        doi = doi.removeprefix("https://doi.org/")
    return doi


def _build_row_key(row):
    normalized_doi = _normalize_doi(row.get(DOI_COLUMN, ""))
    if normalized_doi:
        return f"doi:{normalized_doi}"

    normalized_title = _normalize_title(row.get(PAPER_NAME_COLUMN, ""))
    if normalized_title:
        return f"title:{normalized_title}"

    return ""


def _deduplicate_pass_rows(dataframe):
    deduplicated = dataframe.copy()
    deduplicated[ROW_KEY_COLUMN] = deduplicated.apply(_build_row_key, axis=1)
    deduplicated[DISPLAY_NAME_COLUMN] = deduplicated[PAPER_NAME_COLUMN].map(_normalize_scalar)
    deduplicated = deduplicated[deduplicated[ROW_KEY_COLUMN].ne("")]
    deduplicated = deduplicated.drop_duplicates(subset=ROW_KEY_COLUMN, keep="first")
    deduplicated = deduplicated.set_index(ROW_KEY_COLUMN, drop=True)
    deduplicated.index.name = ROW_KEY_COLUMN
    return deduplicated


def _display_name_map(dataframe):
    return dataframe[DISPLAY_NAME_COLUMN].to_dict()


def _load_pass_dataframe(csv_path):
    dataframe = scleaned_pandas(str(csv_path))
    dataframe.columns = [str(column).strip() for column in dataframe.columns]

    if PAPER_NAME_COLUMN not in dataframe.columns:
        raise ValueError(f"Missing required column: {PAPER_NAME_COLUMN}")

    dataframe[PAPER_NAME_COLUMN] = dataframe[PAPER_NAME_COLUMN].map(_normalize_scalar)
    return _deduplicate_pass_rows(dataframe)


def load_pass_pair(first_pass_path=DEFAULT_FIRST_PASS, second_pass_path=DEFAULT_SECOND_PASS):
    return _load_pass_dataframe(first_pass_path), _load_pass_dataframe(second_pass_path)


def get_overlap_summary(first_pass_path=DEFAULT_FIRST_PASS, second_pass_path=DEFAULT_SECOND_PASS):
    first_pass, second_pass = load_pass_pair(first_pass_path, second_pass_path)
    first_keys = set(first_pass.index)
    second_keys = set(second_pass.index)
    first_names = _display_name_map(first_pass)
    second_names = _display_name_map(second_pass)
    matched_keys = sorted(first_keys & second_keys)

    return {
        "first_pass_papers": len(first_pass),
        "second_pass_papers": len(second_pass),
        "matched_papers": len(matched_keys),
        "first_only_papers": sorted(first_names[key] for key in first_keys - second_keys),
        "second_only_papers": sorted(second_names[key] for key in second_keys - first_keys),
    }


def get_comparison_fields(first_pass, second_pass, scope="all"):
    scope_name = scope.lower()
    shared_fields = [
        column
        for column in first_pass.columns
        if column in second_pass.columns and column not in {ROW_KEY_COLUMN, DISPLAY_NAME_COLUMN}
    ]

    if scope_name == "fair":
        return [field for field in FAIR_FIELDS if field in shared_fields]
    if scope_name == "all":
        return [field for field in shared_fields if field not in EXCLUDED_ALL_FIELDS]

    raise ValueError("scope must be 'all' or 'fair'")


def _resolve_paper_key(first_pass, second_pass, paper_name):
    normalized_name = _normalize_scalar(paper_name)
    candidate_keys = []

    normalized_doi = _normalize_doi(normalized_name)
    if normalized_doi:
        candidate_keys.append(f"doi:{normalized_doi}")

    normalized_title = _normalize_title(normalized_name)
    if normalized_title:
        candidate_keys.append(f"title:{normalized_title}")

    for candidate_key in candidate_keys:
        if candidate_key in first_pass.index and candidate_key in second_pass.index:
            return candidate_key

    if not candidate_keys:
        raise KeyError(f"Paper '{normalized_name}' was not found in either pass")

    selected_key = candidate_keys[0]
    missing_from = []

    if selected_key not in first_pass.index:
        missing_from.append(PASS_LABELS[0])
    if selected_key not in second_pass.index:
        missing_from.append(PASS_LABELS[1])

    if missing_from:
        raise KeyError(f"Paper '{normalized_name}' is missing from: {', '.join(missing_from)}")

    return selected_key


def _build_comparison_rows(first_pass, second_pass, row_key, fields, differences_only):
    rows = []
    display_name = _normalize_scalar(first_pass.at[row_key, DISPLAY_NAME_COLUMN])

    for field in fields:
        first_value = _normalize_scalar(first_pass.at[row_key, field]) if field in first_pass.columns else ""
        second_value = _normalize_scalar(second_pass.at[row_key, field]) if field in second_pass.columns else ""
        matches = first_value == second_value

        if differences_only and matches:
            continue

        rows.append(
            {
                PAPER_NAME_COLUMN: display_name,
                "Field": field,
                PASS_LABELS[0]: first_value,
                PASS_LABELS[1]: second_value,
                "Matches": matches,
                "FAIR Letter": FAIR_LETTER_BY_FIELD.get(field, ""),
            }
        )

    return rows


def compare_paper_marks(
    paper_name,
    first_pass_path=DEFAULT_FIRST_PASS,
    second_pass_path=DEFAULT_SECOND_PASS,
    scope="all",
    differences_only=True,
):
    first_pass, second_pass = load_pass_pair(first_pass_path, second_pass_path)
    row_key = _resolve_paper_key(first_pass, second_pass, paper_name)
    fields = get_comparison_fields(first_pass, second_pass, scope=scope)

    comparison = pd.DataFrame(
        _build_comparison_rows(
            first_pass=first_pass,
            second_pass=second_pass,
            row_key=row_key,
            fields=fields,
            differences_only=differences_only,
        )
    )

    if comparison.empty:
        return pd.DataFrame(columns=[PAPER_NAME_COLUMN, "Field", *PASS_LABELS, "Matches", "FAIR Letter"])

    return comparison.sort_values(["FAIR Letter", "Field"], kind="stable").reset_index(drop=True)


def compare_all_papers(
    first_pass_path=DEFAULT_FIRST_PASS,
    second_pass_path=DEFAULT_SECOND_PASS,
    scope="all",
    differences_only=True,
):
    first_pass, second_pass = load_pass_pair(first_pass_path, second_pass_path)
    matched_keys = sorted(set(first_pass.index) & set(second_pass.index))
    fields = get_comparison_fields(first_pass, second_pass, scope=scope)

    rows = []
    for row_key in matched_keys:
        rows.extend(
            _build_comparison_rows(
                first_pass=first_pass,
                second_pass=second_pass,
                row_key=row_key,
                fields=fields,
                differences_only=differences_only,
            )
        )

    comparison = pd.DataFrame(rows)
    if comparison.empty:
        return pd.DataFrame(columns=[PAPER_NAME_COLUMN, "Field", *PASS_LABELS, "Matches", "FAIR Letter"])

    return comparison.sort_values([PAPER_NAME_COLUMN, "FAIR Letter", "Field"], kind="stable").reset_index(drop=True)


def summarize_disagreements(comparison_dataframe):
    if comparison_dataframe.empty:
        return pd.DataFrame(columns=[PAPER_NAME_COLUMN, "Differences", "FAIR Differences"])

    summary = (
        comparison_dataframe.assign(
            is_fair_field=comparison_dataframe["FAIR Letter"].ne("")
        )
        .groupby(PAPER_NAME_COLUMN, as_index=False)
        .agg(
            Differences=("Field", "count"),
            FAIR_Differences=("is_fair_field", "sum"),
        )
        .rename(columns={"FAIR_Differences": "FAIR Differences"})
        .sort_values(["Differences", "FAIR Differences", PAPER_NAME_COLUMN], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    return summary