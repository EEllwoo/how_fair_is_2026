"""Utilities for building first/second/optimistic FAIR plotting datasets."""

import re
import pandas as pd

from processing_scripts.fix_missing_information import normalize_text
from processing_scripts.pre_process import scleaned_pandas

ARTIFACT_COLUMN = "Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?"
DOI_COLUMN = "DOI (of paper)"
ROW_KEY_COLUMN = "__row_key"
DISPLAY_NAME_COLUMN = "__display_name"
DEFAULT_LOCATION_COLUMNS = [
    "Link to artefact repository (Github, Zenodo, Figshare etc)",
    "Please input any links to GitHub if available",
]
DEFAULT_DROP_COLUMNS = [
    "A1 follow-up: Which of these protocols are available to download the software?",
    "R2 follow-up: Is there a file / project manager tool to help with the installation of other software / libraries?",
    "Is the software itself documented well?",
    "Which of the following code readability standards have been implemented?",
    "How long did this form take to complete?",
    "Anything else to note?",
    "Any additional notes for F?",
    "Any additional notes for A?",
    "Any additional notes for I?",
    "Any additional notes for R?",
]
COMPLIANT_VALUES = {"Yes", "Not Applicable", "Not necessary", "Software is currently available"}


def _normalize_scalar(value):
    if isinstance(value, pd.Series):
        for item in value.tolist():
            normalized_item = _normalize_scalar(item)
            if normalized_item:
                return normalized_item
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip().replace("\u2013", "-")


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

    normalized_title = _normalize_title(row.get("Paper Name:", ""))
    if normalized_title:
        return f"title:{normalized_title}"

    return ""


def _keyed_pass(dataframe):
    keyed = dataframe.copy()
    keyed[ROW_KEY_COLUMN] = keyed.apply(_build_row_key, axis=1)
    keyed[DISPLAY_NAME_COLUMN] = keyed.index.map(_normalize_scalar)
    keyed = keyed[keyed[ROW_KEY_COLUMN].ne("")]
    keyed = keyed.drop_duplicates(subset=ROW_KEY_COLUMN, keep="first")
    keyed = keyed.set_index(ROW_KEY_COLUMN, drop=True)
    keyed.index.name = ROW_KEY_COLUMN
    return keyed


def load_pass_dataset(
    csv_file,
    drop_cols=None,
    index_col="Paper Name:",
    artifact_col=ARTIFACT_COLUMN,
    artifacts_only=False,
):
    """Load one pass, drop optional columns, and optionally keep only rows with artifacts present."""
    if drop_cols is None:
        drop_cols = DEFAULT_DROP_COLUMNS

    available_cols = pd.read_csv(csv_file, nrows=0).columns
    columns_to_drop = [col for col in drop_cols if col in available_cols]

    df = scleaned_pandas(
        csv_file,
        columns_to_drop=columns_to_drop,
        index_col=index_col,
    )

    if artifact_col not in df.columns:
        raise ValueError(f"Missing expected column: {artifact_col}")

    if artifacts_only:
        return df[df[artifact_col].astype(str).str.strip().str.lower() == "yes"]
    return df


def load_filtered_pass(csv_file, drop_cols=None, index_col="Paper Name:", artifact_col=ARTIFACT_COLUMN):
    """Backward-compatible helper to load one pass and keep only rows with artifacts present."""
    return load_pass_dataset(
        csv_file,
        drop_cols=drop_cols,
        index_col=index_col,
        artifact_col=artifact_col,
        artifacts_only=True,
    )


def _row_for_paper(frame, paper_name):
    if paper_name not in frame.index:
        return pd.Series(dtype=object)
    row = frame.loc[paper_name]
    if isinstance(row, pd.DataFrame):
        return row.iloc[0]
    return row


def _is_compliant(value):
    return str(value).strip() in COMPLIANT_VALUES


def _pick_optimistic_mark(first_value, second_value):
    if _is_compliant(first_value):
        return first_value
    if _is_compliant(second_value):
        return second_value

    first_text = "" if pd.isna(first_value) else str(first_value).strip()
    second_text = "" if pd.isna(second_value) else str(second_value).strip()

    # Prefer a real value over "Artefact Unavailable" — if one pass found the
    # artifact, the optimistic result should reflect that.
    first_unavailable = first_text == "Artefact Unavailable"
    second_unavailable = second_text == "Artefact Unavailable"

    if first_text and not first_unavailable:
        return first_value
    if second_text and not second_unavailable:
        return second_value
    if first_text:
        return first_value
    if second_text:
        return second_value
    return first_value


def _merge_locations(first_value, second_value):
    def _split_values(value):
        if pd.isna(value):
            return []
        text = str(value).strip()
        if not text:
            return []
        return [part.strip() for part in re.split(r"[|,;\\n]+", text) if part.strip()]

    merged = []
    seen = set()
    for part in _split_values(first_value) + _split_values(second_value):
        key = part.lower()
        if key not in seen:
            seen.add(key)
            merged.append(part)
    return " | ".join(merged)


def build_optimistic_dataset(
    first_pass_df,
    second_pass_df,
    fair_criteria,
    artifact_col=ARTIFACT_COLUMN,
    location_columns=None,
    artifacts_only=True,
):
    """Build optimistic pass where criteria are OR-combined across the two passes."""
    if location_columns is None:
        location_columns = DEFAULT_LOCATION_COLUMNS

    first_keyed = _keyed_pass(first_pass_df)
    second_keyed = _keyed_pass(second_pass_df)

    optimistic_rows = []
    optimistic_index = []

    for row_key in first_keyed.index.union(second_keyed.index):
        first_row = _row_for_paper(first_keyed, row_key)
        second_row = _row_for_paper(second_keyed, row_key)

        if first_row.empty:
            combined = second_row.copy()
        elif second_row.empty:
            combined = first_row.copy()
        else:
            combined = first_row.combine_first(second_row)

        for criterion in fair_criteria:
            if criterion in combined.index:
                combined[criterion] = _pick_optimistic_mark(
                    first_row.get(criterion, pd.NA),
                    second_row.get(criterion, pd.NA),
                )

        if artifact_col in combined.index:
            first_has_artifact = str(first_row.get(artifact_col, "")).strip().lower() == "yes"
            second_has_artifact = str(second_row.get(artifact_col, "")).strip().lower() == "yes"
            combined[artifact_col] = "Yes" if (first_has_artifact or second_has_artifact) else "No"

        for location_col in location_columns:
            if location_col in combined.index:
                combined[location_col] = _merge_locations(
                    first_row.get(location_col, pd.NA),
                    second_row.get(location_col, pd.NA),
                )

        display_name = _normalize_scalar(
            first_row.get(DISPLAY_NAME_COLUMN, "") or second_row.get(DISPLAY_NAME_COLUMN, "")
        )
        optimistic_index.append(display_name or row_key)
        optimistic_rows.append(combined)

    df_optimistic = pd.DataFrame(optimistic_rows, index=optimistic_index)
    df_optimistic.index.name = "Paper Name:"

    if artifacts_only:
        return df_optimistic[df_optimistic[artifact_col].astype(str).str.strip().str.lower() == "yes"]
    return df_optimistic


def get_dataset_size_table(first_pass_df, second_pass_df, optimistic_df):
    """Return a compact table of dataset sizes for quick sanity checks."""
    return pd.DataFrame(
        [
            {"dataset": "first_pass", "papers": len(first_pass_df)},
            {"dataset": "second_pass", "papers": len(second_pass_df)},
            {"dataset": "optimistic", "papers": len(optimistic_df)},
        ]
    )
