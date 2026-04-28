from datetime import datetime
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


def _match_key_by_title(dataframe, normalized_title):
    title_matches = dataframe[dataframe[DISPLAY_NAME_COLUMN].map(_normalize_title).eq(normalized_title)]
    if title_matches.empty:
        return None
    return title_matches.index[0]


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

        first_title_key = _match_key_by_title(first_pass, normalized_title)
        second_title_key = _match_key_by_title(second_pass, normalized_title)
        if first_title_key is not None and first_title_key == second_title_key:
            return first_title_key

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


def _display_response(value):
    normalized_value = _normalize_scalar(value)
    return normalized_value if normalized_value else "<blank>"


def build_field_conflict_summary(
    first_pass_path=DEFAULT_FIRST_PASS,
    second_pass_path=DEFAULT_SECOND_PASS,
    scope="all",
):
    comparison_dataframe = compare_all_papers(
        first_pass_path=first_pass_path,
        second_pass_path=second_pass_path,
        scope=scope,
        differences_only=False,
    )

    if comparison_dataframe.empty:
        return pd.DataFrame(columns=["Field", "Compared", "Conflicts", "Agreements", "Conflict Rate"])

    summary = (
        comparison_dataframe.groupby("Field", as_index=False)
        .agg(
            Compared=("Matches", "size"),
            Conflicts=("Matches", lambda values: int((~values).sum())),
            Agreements=("Matches", "sum"),
        )
        .sort_values(["Conflicts", "Compared", "Field"], ascending=[False, False, True])
        .reset_index(drop=True)
    )
    summary["Conflict Rate"] = (summary["Conflicts"] / summary["Compared"]).round(3)
    return summary[["Field", "Compared", "Conflicts", "Agreements", "Conflict Rate"]]


def build_reviewer_confusion_matrix(
    first_pass_path=DEFAULT_FIRST_PASS,
    second_pass_path=DEFAULT_SECOND_PASS,
    scope="all",
    field=None,
):
    comparison_dataframe = compare_all_papers(
        first_pass_path=first_pass_path,
        second_pass_path=second_pass_path,
        scope=scope,
        differences_only=False,
    )

    if field is not None:
        comparison_dataframe = comparison_dataframe[comparison_dataframe["Field"].eq(field)]

    if comparison_dataframe.empty:
        return pd.DataFrame()

    first_values = comparison_dataframe[PASS_LABELS[0]].map(_display_response)
    second_values = comparison_dataframe[PASS_LABELS[1]].map(_display_response)

    confusion_matrix = pd.crosstab(
        first_values,
        second_values,
        rownames=[PASS_LABELS[0]],
        colnames=[PASS_LABELS[1]],
    )
    return confusion_matrix.sort_index(axis=0).sort_index(axis=1)


def build_conflict_overview(overlap_summary, all_field_differences, fair_field_differences):
    return {
        "matched_papers": overlap_summary["matched_papers"],
        "first_only_papers": len(overlap_summary["first_only_papers"]),
        "second_only_papers": len(overlap_summary["second_only_papers"]),
        "papers_with_any_conflict": all_field_differences[PAPER_NAME_COLUMN].nunique(),
        "papers_with_fair_conflict": fair_field_differences[PAPER_NAME_COLUMN].nunique(),
        "total_field_conflicts": len(all_field_differences),
        "total_fair_conflicts": len(fair_field_differences),
    }


def build_paper_conflict_report(comparison_dataframe):
    if comparison_dataframe.empty:
        return pd.DataFrame(
            columns=[PAPER_NAME_COLUMN, "Differences", "FAIR Differences", "FAIR Letters", "Example Fields"]
        )

    summary = summarize_disagreements(comparison_dataframe)
    details = (
        comparison_dataframe.groupby(PAPER_NAME_COLUMN, as_index=False)
        .agg(
            FAIR_Letters=(
                "FAIR Letter",
                lambda values: ", ".join(sorted({value for value in values if value})),
            ),
            Example_Fields=(
                "Field",
                lambda values: "; ".join(list(values)[:5]),
            ),
        )
        .rename(columns={"FAIR_Letters": "FAIR Letters", "Example_Fields": "Example Fields"})
    )

    return summary.merge(details, on=PAPER_NAME_COLUMN, how="left")


def build_conflict_report_markdown(
    overview,
    paper_conflict_report,
    fair_conflict_report,
    overlap_summary,
    top_n=10,
):
    lines = [
        "# Pass Conflict Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Overview",
        "",
        f"- Matched papers compared: {overview['matched_papers']}",
        f"- Papers only in first pass: {overview['first_only_papers']}",
        f"- Papers only in second pass: {overview['second_only_papers']}",
        f"- Papers with any conflict: {overview['papers_with_any_conflict']}",
        f"- Papers with FAIR conflicts: {overview['papers_with_fair_conflict']}",
        f"- Total field conflicts: {overview['total_field_conflicts']}",
        f"- Total FAIR conflicts: {overview['total_fair_conflicts']}",
        "",
        f"## Top {min(top_n, len(paper_conflict_report))} Papers By Total Conflicts",
        "",
    ]

    top_conflicts = paper_conflict_report.head(top_n)
    if top_conflicts.empty:
        lines.append("No conflicts found.")
    else:
        for _, row in top_conflicts.iterrows():
            fair_letters = row["FAIR Letters"] or "None"
            lines.append(
                f"- {row[PAPER_NAME_COLUMN]}: {row['Differences']} conflicts, {row['FAIR Differences']} FAIR conflicts, letters {fair_letters}."
            )

    lines.extend(["", f"## Top {min(top_n, len(fair_conflict_report))} Papers By FAIR Conflicts", ""])

    top_fair_conflicts = fair_conflict_report.head(top_n)
    if top_fair_conflicts.empty:
        lines.append("No FAIR conflicts found.")
    else:
        for _, row in top_fair_conflicts.iterrows():
            fair_letters = row["FAIR Letters"] or "None"
            lines.append(
                f"- {row[PAPER_NAME_COLUMN]}: {row['FAIR Differences']} FAIR conflicts across letters {fair_letters}."
            )

    if overlap_summary["first_only_papers"]:
        lines.extend(["", "## First Pass Only", ""])
        lines.extend(f"- {paper}" for paper in overlap_summary["first_only_papers"])

    if overlap_summary["second_only_papers"]:
        lines.extend(["", "## Second Pass Only", ""])
        lines.extend(f"- {paper}" for paper in overlap_summary["second_only_papers"])

    return "\n".join(lines)


def export_conflict_report(
    first_pass_path=DEFAULT_FIRST_PASS,
    second_pass_path=DEFAULT_SECOND_PASS,
    output_dir=PROJECT_ROOT / "results" / "conflict_reports",
    top_n=10,
):
    overlap_summary = get_overlap_summary(first_pass_path, second_pass_path)
    all_field_differences = compare_all_papers(
        first_pass_path=first_pass_path,
        second_pass_path=second_pass_path,
        scope="all",
        differences_only=True,
    )
    fair_field_differences = compare_all_papers(
        first_pass_path=first_pass_path,
        second_pass_path=second_pass_path,
        scope="fair",
        differences_only=True,
    )

    overview = build_conflict_overview(overlap_summary, all_field_differences, fair_field_differences)
    paper_conflict_report = build_paper_conflict_report(all_field_differences)
    fair_conflict_report = build_paper_conflict_report(fair_field_differences)
    markdown_report = build_conflict_report_markdown(
        overview=overview,
        paper_conflict_report=paper_conflict_report,
        fair_conflict_report=fair_conflict_report,
        overlap_summary=overlap_summary,
        top_n=top_n,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_conflicts_path = output_dir / "all_field_conflicts.csv"
    fair_conflicts_path = output_dir / "fair_field_conflicts.csv"
    paper_summary_path = output_dir / "paper_conflict_summary.csv"
    fair_summary_path = output_dir / "fair_conflict_summary.csv"
    markdown_path = output_dir / "conflict_report.md"

    all_field_differences.to_csv(all_conflicts_path, index=False)
    fair_field_differences.to_csv(fair_conflicts_path, index=False)
    paper_conflict_report.to_csv(paper_summary_path, index=False)
    fair_conflict_report.to_csv(fair_summary_path, index=False)
    markdown_path.write_text(markdown_report, encoding="utf-8")

    return {
        "overview": overview,
        "all_field_differences": all_field_differences,
        "fair_field_differences": fair_field_differences,
        "paper_conflict_report": paper_conflict_report,
        "fair_conflict_report": fair_conflict_report,
        "markdown_report": markdown_report,
        "output_paths": {
            "all_field_conflicts": all_conflicts_path,
            "fair_field_conflicts": fair_conflicts_path,
            "paper_conflict_summary": paper_summary_path,
            "fair_conflict_summary": fair_summary_path,
            "markdown_report": markdown_path,
        },
    }