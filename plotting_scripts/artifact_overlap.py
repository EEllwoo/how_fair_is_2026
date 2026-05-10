"""Plot artifact overlap between first and second pass."""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import cm
from matplotlib.colors import Normalize
from processing_scripts.pre_process import scleaned_pandas
from processing_scripts.optimistic_dataset import _keyed_pass, COMPLIANT_VALUES, DISPLAY_NAME_COLUMN
from plotting_scripts.fair_letter_compliance import save_plot
from plotting_scripts.palette import IBM_BLUE, IBM_PURPLE, ibm_colormap


def _fair_criteria_count(row, fair_criteria):
    """Return the count of FAIR criteria that are compliant for a row."""
    return sum(
        str(row.get(c, "")).strip() in COMPLIANT_VALUES
        for c in fair_criteria
        if c in row.index
    )


def _print_single_pass_details(label, keys, keyed_df, fair_criteria):
    """Print average FAIR criteria count and plot repository locations for single-pass papers."""
    from plotting_scripts.repository_stats import get_repo_stats_available, plot_graph

    _cited_col = "Has the software artefact been mentioned or cited in the paper for ease of findability?"

    if not keys:
        print(f"\n--- Found in {label} only: 0 papers ---")
        return

    subset = keyed_df.loc[keys].copy()
    # Restore the index to "Paper Name:" so get_repo_stats_available can iterate rows normally
    subset.index.name = "Paper Name:"

    counts = [_fair_criteria_count(row, fair_criteria) for _, row in subset.iterrows()]
    avg = sum(counts) / len(counts) if counts else 0

    cited_count = 0
    if _cited_col in subset.columns:
        cited_count = sum(str(v).strip().lower() == "yes" for v in subset[_cited_col])

    print(f"\n--- Found in {label} only ({len(keys)} papers) ---")
    print(f"  Artefact cited in paper for findability: {cited_count} / {len(keys)}")
    print(f"  Average FAIR criteria met: {avg:.1f} / {len(fair_criteria)}")

    available_stats, unavailable_stats = get_repo_stats_available(subset)
    plot_graph(
        available_stats,
        title=f"Repository Service Counts ({label} only — available artefacts)",
        label1=label,
    )
    plot_graph(
        unavailable_stats,
        title=f"Repository Service Counts ({label} only — unavailable artefacts)",
        label1=label,
    )


def _load_overlap_df(data_source, default_csv):
    """Load overlap data from DataFrame or CSV path."""
    if isinstance(data_source, pd.DataFrame):
        return data_source.copy()
    if data_source is None:
        return scleaned_pandas(default_csv, index_col="Paper Name:")
    return scleaned_pandas(data_source, index_col="Paper Name:")


def plot_artifact_overlap(
    first_pass_df=None,
    second_pass_df=None,
    first_label="First",
    second_label="Second",
    exclude_no_artifact_papers=True,
    fair_criteria=None,
):
    """
    Generate table visualization showing artifact overlap between first and second pass evaluations.
    """
    artifact_column = "Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?"
    f1_column = "F1. Software is assigned a globally unique and persistent identifier (DOI)"

    first_pass_df = _load_overlap_df(first_pass_df, "results/FAIR Evaluation Results - First Pass Responses_fixed.csv")
    second_pass_df = _load_overlap_df(second_pass_df, "results/FAIR Evaluation Results - Second Pass Responses_fixed.csv")

    if artifact_column not in first_pass_df.columns or artifact_column not in second_pass_df.columns:
        raise ValueError(f"Missing expected artifact column: {artifact_column}")

    first_pass_keyed = _keyed_pass(first_pass_df)
    second_pass_keyed = _keyed_pass(second_pass_df)
    matched_keys = sorted(set(first_pass_keyed.index) | set(second_pass_keyed.index))

    found_in_both = 0
    found_in_first_only = 0
    found_in_second_only = 0
    found_in_neither = 0
    first_only_keys = []
    second_only_keys = []

    def _is_unavailable(keyed_df, row_key):
        """Return True if this pass marked the artifact as unavailable (F1 = 'Artefact Unavailable')."""
        if row_key not in keyed_df.index or f1_column not in keyed_df.columns:
            return False
        return str(keyed_df.at[row_key, f1_column]).strip() == "Artefact Unavailable"

    def _artifact_found(keyed_df, row_key):
        """Artifact was accessible: artifact col is Yes and F1 is not 'Artefact Unavailable'."""
        if row_key not in keyed_df.index:
            return False
        has_artifact = str(keyed_df.at[row_key, artifact_column]).strip().lower() == "yes"
        return has_artifact and not _is_unavailable(keyed_df, row_key)

    def _should_have_artifact(keyed_df, row_key):
        """Paper should have an artifact: either reported Yes or was marked Artefact Unavailable."""
        if row_key not in keyed_df.index:
            return False
        has_artifact = str(keyed_df.at[row_key, artifact_column]).strip().lower() == "yes"
        return has_artifact or _is_unavailable(keyed_df, row_key)

    for row_key in matched_keys:
        found_in_first = _artifact_found(first_pass_keyed, row_key)
        found_in_second = _artifact_found(second_pass_keyed, row_key)

        paper_should_have_artifact = (
            _should_have_artifact(first_pass_keyed, row_key)
            or _should_have_artifact(second_pass_keyed, row_key)
        )

        if exclude_no_artifact_papers and not paper_should_have_artifact:
            continue

        if found_in_first and found_in_second:
            found_in_both += 1
        elif found_in_first and not found_in_second:
            found_in_first_only += 1
            first_only_keys.append(row_key)
        elif not found_in_first and found_in_second:
            found_in_second_only += 1
            second_only_keys.append(row_key)
        else:
            found_in_neither += 1

    total_with_artifact = found_in_both + found_in_first_only + found_in_second_only + found_in_neither
    print(f"Papers with tool/repo mentioned: {total_with_artifact} / {len(matched_keys)}")

    _cited_col = "Has the software artefact been mentioned or cited in the paper for ease of findability?"

    def _is_cited(keyed_df, row_key):
        if row_key not in keyed_df.index or _cited_col not in keyed_df.columns:
            return False
        return str(keyed_df.at[row_key, _cited_col]).strip().lower() == "yes"

    papers_cited = sum(
        _is_cited(first_pass_keyed, k) or _is_cited(second_pass_keyed, k)
        for k in matched_keys
        if _should_have_artifact(first_pass_keyed, k) or _should_have_artifact(second_pass_keyed, k)
    )
    print(f"Artefact cited in paper for findability: {papers_cited} / {total_with_artifact}")

    if fair_criteria:
        all_scores = []
        for row_key in matched_keys:
            row = (
                first_pass_keyed.loc[row_key]
                if row_key in first_pass_keyed.index
                else second_pass_keyed.loc[row_key]
            )
            paper_should_have_artifact = (
                _should_have_artifact(first_pass_keyed, row_key)
                or _should_have_artifact(second_pass_keyed, row_key)
            )
            if paper_should_have_artifact:
                all_scores.append(_fair_criteria_count(row, fair_criteria))
        if all_scores:
            print(f"Set-wide average FAIR criteria met: {sum(all_scores) / len(all_scores):.1f} / {len(fair_criteria)}")

    overlap_matrix = np.array([
        [found_in_both, found_in_first_only],
        [found_in_second_only, found_in_neither],
    ])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis("off")

    norm = Normalize(vmin=0, vmax=max(overlap_matrix.max(), 1))
    cmap = ibm_colormap("ibm_overlap", [IBM_BLUE, IBM_PURPLE])
    cell_colours = [[cmap(norm(value)) for value in row] for row in overlap_matrix]
    cell_text = [
        [f"{found_in_both}\n(found in both)", f"{found_in_first_only}\n(first only)"],
        [f"{found_in_second_only}\n(second only)", f"{found_in_neither}\n(neither)"],
    ]

    table = ax.table(
        cellText=cell_text,
        cellColours=cell_colours,
        rowLabels=[f"Found in {first_label}", f"Not Found in {first_label}"],
        colLabels=[f"Found in {second_label}", f"Not Found in {second_label}"],
        cellLoc="center",
        loc="center",
        bbox=[0.12, 0.12, 0.90, 0.90],
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)

    for (row_index, col_index), cell in table.get_celld().items():
        cell.set_linewidth(0)
        if row_index >= 1 and col_index >= 0:
            value = overlap_matrix[row_index - 1, col_index]
            text_color = "white" if value > overlap_matrix.max() * 0.5 else "black"
            cell.get_text().set_color(text_color)
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor("white")
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_color("black")

    ax.set_title(f"Artifact Overlap Between {first_label} and {second_label}", fontsize=14, fontweight="bold", pad=5)

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    plt.tight_layout()
    save_plot(fig)
    plt.show()

    if fair_criteria:
        _print_single_pass_details(first_label, first_only_keys, first_pass_keyed, fair_criteria)
        _print_single_pass_details(second_label, second_only_keys, second_pass_keyed, fair_criteria)
