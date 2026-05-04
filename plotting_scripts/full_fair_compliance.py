"""Plot full FAIR compliance distribution."""

import matplotlib.pyplot as plt
from plotting_scripts.FAIR_compliance import calculate_full_fair_compliance, F
from plotting_scripts.fair_letter_compliance import save_plot


ARTIFACT_COLUMN = "Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?"
UNAVAILABLE_MARK = "Artefact Unavailable"


def plot_full_fair_compliance(df_first, df_second, df_optimistic):
    """
    Generate a bar chart comparing full FAIR compliance across datasets.
    
    Args:
        df_first: DataFrame for first pass
        df_second: DataFrame for second pass
        df_optimistic: DataFrame for optimistic pass
    """
    datasets = [
        ("First pass", df_first),
        ("Second pass", df_second),
        ("Optimistic", df_optimistic),
    ]

    unavailable_column = F[0]
    labels = []
    fully_compliant_counts = []
    not_compliant_counts = []
    artifact_unavailable_counts = []
    no_tool_counts = []
    totals = []

    for label, df in datasets:
        tool_yes = df[ARTIFACT_COLUMN].astype(str).str.strip().str.lower() == "yes"
        unavailable = df[unavailable_column].astype(str).str.strip() == UNAVAILABLE_MARK

        no_tool_mask = ~tool_yes
        artifact_unavailable_mask = tool_yes & unavailable
        assessable_mask = tool_yes & ~unavailable

        assessable_df = df[assessable_mask]
        compliant_papers, _ = calculate_full_fair_compliance(assessable_df)
        compliant_count = len(compliant_papers)
        assessable_total = len(assessable_df)
        not_compliant_count = assessable_total - compliant_count

        labels.append(label)
        fully_compliant_counts.append(compliant_count)
        not_compliant_counts.append(not_compliant_count)
        artifact_unavailable_counts.append(int(artifact_unavailable_mask.sum()))
        no_tool_counts.append(int(no_tool_mask.sum()))
        totals.append(len(df))

    fig, ax = plt.subplots(figsize=(11, 6.5))

    category_data = [
        ("Fully FAIR compliant", fully_compliant_counts, "#59A14F"),
        ("Not fully compliant", not_compliant_counts, "#E15759"),
        ("Artifact not available", artifact_unavailable_counts, "#F28E2B"),
        ("No tool mentioned", no_tool_counts, "#9C755F"),
    ]

    cumulative_bottom = [0, 0, 0]
    for category_label, category_values, color in category_data:
        bars = ax.bar(
            labels,
            category_values,
            bottom=cumulative_bottom,
            label=category_label,
            color=color,
            edgecolor="black",
            linewidth=0.6,
            alpha=0.9,
        )

        for idx, bar in enumerate(bars):
            if category_values[idx] > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    cumulative_bottom[idx] + category_values[idx] / 2,
                    str(category_values[idx]),
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white",
                    fontweight="bold",
                )

        cumulative_bottom = [
            cumulative_bottom[idx] + category_values[idx] for idx in range(len(cumulative_bottom))
        ]

    for idx, total in enumerate(totals):
        ax.text(
            idx,
            total + max(totals) * 0.01,
            f"Total: {total}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_ylim(0, max(totals) * 1.12 if totals else 1)
    ax.set_ylabel("Paper count", fontsize=11)
    ax.set_xlabel("Dataset", fontsize=11)
    ax.set_title("Full FAIR Outcome Breakdown Across Datasets", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.25)

    plt.tight_layout()
    save_plot(fig)
    plt.style.use("ggplot")
    plt.show()
