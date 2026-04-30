"""Plot artifact overlap between first and second pass."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from processing_scripts.pre_process import scleaned_pandas
from plotting_scripts.fair_letter_compliance import save_plot


def plot_artifact_overlap():
    """
    Generate table visualization showing artifact overlap between first and second pass evaluations.
    """
    artifact_column = "Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?"

    first_pass_df = scleaned_pandas(
        "results/FAIR Evaluation Results - First Pass Responses_fixed.csv",
        index_col="Paper Name:",
    )
    second_pass_df = scleaned_pandas(
        "results/FAIR Evaluation Results - Second Pass Responses_fixed.csv",
        index_col="Paper Name:",
    )

    if artifact_column not in first_pass_df.columns or artifact_column not in second_pass_df.columns:
        raise ValueError(f"Missing expected artifact column: {artifact_column}")

    matched_keys = sorted(set(first_pass_df.index) & set(second_pass_df.index))

    found_in_both = 0
    found_in_first_only = 0
    found_in_second_only = 0
    found_in_neither = 0

    for row_key in matched_keys:
        found_in_first = str(first_pass_df.at[row_key, artifact_column]).strip().lower() == "yes"
        found_in_second = str(second_pass_df.at[row_key, artifact_column]).strip().lower() == "yes"

        if found_in_first and found_in_second:
            found_in_both += 1
        elif found_in_first and not found_in_second:
            found_in_first_only += 1
        elif not found_in_first and found_in_second:
            found_in_second_only += 1
        else:
            found_in_neither += 1

    overlap_matrix = np.array([
        [found_in_both, found_in_first_only],
        [found_in_second_only, found_in_neither],
    ])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axis("off")

    norm = Normalize(vmin=0, vmax=max(overlap_matrix.max(), 1))
    cmap = plt.get_cmap("Blues")
    cell_colours = [[cmap(norm(value)) for value in row] for row in overlap_matrix]
    cell_text = [
        [f"{found_in_both}\n(found in both)", f"{found_in_first_only}\n(first only)"],
        [f"{found_in_second_only}\n(second only)", f"{found_in_neither}\n(neither)"],
    ]

    table = ax.table(
        cellText=cell_text,
        cellColours=cell_colours,
        rowLabels=["Found in First", "Not Found in First"],
        colLabels=["Found in Second", "Not Found in Second"],
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

    ax.set_title("Artifact Overlap Between First and Second Pass", fontsize=14, fontweight="bold", pad=5)

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])

    plt.tight_layout()
    save_plot(fig)
    plt.show()
