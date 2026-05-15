"""Plot distribution of FAIR criteria met per paper."""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import Normalize, PowerNorm
from plotting_scripts.FAIR_compliance import is_criterion_compliant, get_value_safely
from plotting_scripts.fair_letter_compliance import save_plot
from plotting_scripts.palette import IBM_YELLOW, IBM_BLUE, ibm_colormap, get_pgf_rc, FONTSIZE_AXES, FONTSIZE_LABELS, FONTSIZE_TEXT


def plot_fair_criteria_distribution(df, F, A, I, R):
    """
    Generate bar chart showing distribution of papers by number of FAIR criteria met.
    Bar colors indicate DOI proportion within each criteria-count group.
    
    Args:
        df: DataFrame with FAIR evaluation results
        F, A, I, R: Lists of criteria for each FAIR letter
    """
    all_criteria = F + A + I + R
    n_criteria = len(all_criteria)
    doi_criterion = "F1. Software is assigned a globally unique and persistent identifier (DOI)"

    # Compute per-paper counts
    criteria_met_per_paper = []
    has_doi_per_paper = []

    for paper_name in df.index:
        met_count = sum(is_criterion_compliant(df, paper_name, criterion) for criterion in all_criteria)
        criteria_met_per_paper.append(met_count)

        doi_value = get_value_safely(df, paper_name, doi_criterion) if doi_criterion in df.columns else "No"
        has_doi_per_paper.append(str(doi_value).strip().lower() == "yes")

    plot_df = pd.DataFrame({
        "criteria_met": criteria_met_per_paper,
        "has_doi": has_doi_per_paper
    })

    # Build 1..n bins, keeping zero-count bins visible
    group_counts = plot_df["criteria_met"].value_counts().reindex(range(1, n_criteria + 1), fill_value=0)
    doi_counts = plot_df.groupby("criteria_met")["has_doi"].sum().reindex(range(1, n_criteria + 1), fill_value=0)

    # DOI proportion in each group (0 when group is empty)
    doi_proportions = (doi_counts / group_counts.replace(0, np.nan)).fillna(0.0)

    # Color bars by DOI proportion.
    # gamma < 1 expands the low end of the scale, making 0-20% more visually distinct.
    norm = PowerNorm(gamma=0.3, vmin=0, vmax=1)
    cmap = ibm_colormap("ibm_doi_proportion", [IBM_YELLOW, IBM_BLUE])
    bar_colors = cmap(norm(doi_proportions.values))

    fig, ax = plt.subplots(figsize=(16, 6))
    bars = ax.bar(
        group_counts.index,
        group_counts.values,
        color=bar_colors,
        alpha=0.9,
        edgecolor="black"
    )

    ax.set_xlabel("Number of FAIR criteria met", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_ylabel("Number of papers", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_xticks(range(1, n_criteria + 1))

    ax.set_xticklabels(ax.get_xticklabels(), fontsize=FONTSIZE_LABELS)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=FONTSIZE_LABELS)

    # Add paper-count labels on top of bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=FONTSIZE_TEXT,
            )

    # Add DOI proportion labels inside bars when possible
    for x_val, total, doi_prop in zip(group_counts.index, group_counts.values, doi_proportions.values):
        if total > 0:
            ax.text(
                x_val,
                max(total * 0.55, 0.2),
                f"DOI: {doi_prop:.0%}",
                ha="center",
                va="center",
                fontsize=FONTSIZE_TEXT-4,
                color="black",
            )

    # Colorbar legend for DOI proportions
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("DOI proportion in this criteria-count group", fontsize=FONTSIZE_LABELS)


    plt.tight_layout()
    save_plot(fig, title="fair_criteria_distribution")
    plt.style.use("ggplot")
    plt.show()


def main(df=None, F=None, A=None, I=None, R=None):
    """
    Generate FAIR criteria distribution plots.
    
    Args:
        df: DataFrame with FAIR evaluation results (optional).
        F, A, I, R: Lists of criteria for each FAIR letter (optional).
    """
    if df is not None and F is not None and A is not None and I is not None and R is not None:
        print("Generating FAIR criteria distribution plot...")
        plot_fair_criteria_distribution(df, F, A, I, R)


if __name__ == '__main__':
    main()
