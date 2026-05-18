"""Plot ACM badge compliance cascade."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from processing_scripts.pre_process import scleaned_pandas
from plotting_scripts.FAIR_compliance import A, F, I, R, is_criterion_compliant
from plotting_scripts.fair_letter_compliance import save_plot
from plotting_scripts.palette import BADGE_CASCADE_COLORS, get_pgf_rc, FONTSIZE_AXES, FONTSIZE_LABELS, FONTSIZE_LEGEND, FONTSIZE_TEXT


ACM_BADGE_COLUMN = "Which (if any) ACM Badges does the report have?"
BADGE_LEVELS = ["No badge", "Available only", "Available, Functional", "Available, Functional, Reusable"]


def _load_df(data_source):
    """Load plotting data from either an in-memory DataFrame or CSV path."""
    if isinstance(data_source, pd.DataFrame):
        return data_source.copy()
    return scleaned_pandas(data_source, index_col="Paper Name:")


def classify_highest_badge(badge_value):
    """Classify a badge string into the highest ACM badge level awarded."""
    badge_text = str(badge_value).strip().lower()
    has_available = "artefact available" in badge_text
    has_functional = "artefact functional" in badge_text
    has_reusable = "artefact reusable" in badge_text

    if has_available and has_functional and has_reusable:
        return "Available, Functional, Reusable"
    if has_available and has_functional:
        return "Available, Functional"
    if has_available:
        return "Available only"
    return "No badge"


def plot_acm_badge_cascade(data_source):
    """
    Generate bar chart showing ACM badge compliance cascade (no badge -> available -> functional -> reusable).
    
    Args:
        data_source: DataFrame or CSV path with FAIR evaluation results
    """
    wide_df = _load_df(data_source)

    if ACM_BADGE_COLUMN not in wide_df.columns:
        raise ValueError(f"Missing ACM badge column: {ACM_BADGE_COLUMN}")

    badge_levels = wide_df[ACM_BADGE_COLUMN].apply(classify_highest_badge)
    cascade_counts = [int((badge_levels == badge_level).sum()) for badge_level in BADGE_LEVELS]

    fig, ax = plt.subplots(figsize=(16, 6))
    bars = ax.bar(
        BADGE_LEVELS,
        cascade_counts,
        color=BADGE_CASCADE_COLORS,
        edgecolor="black",
        alpha=0.9,
    )

    ax.set_xlabel("Highest ACM Badge Awarded", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_ylabel("Number of papers", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=FONTSIZE_LABELS)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=FONTSIZE_LABELS)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=FONTSIZE_TEXT,
            fontweight='bold'
        )

    plt.tight_layout()
    save_plot(fig, title="acm_badge_cascade")
    plt.show()


def plot_fair_criteria_whisker_by_badge(data_source, fair_criteria=None, no_badge_fraction=0.5, random_state=42):
    """Plot vertical violin distributions of FAIR criteria by ACM badge with mean markers."""
    wide_df = _load_df(data_source)

    if ACM_BADGE_COLUMN not in wide_df.columns:
        raise ValueError(f"Missing ACM badge column: {ACM_BADGE_COLUMN}")

    if fair_criteria is None:
        fair_criteria = F + A + I + R

    badge_levels = wide_df[ACM_BADGE_COLUMN].apply(classify_highest_badge)
    criteria_counts = []
    for paper_name in wide_df.index:
        met_count = sum(
            is_criterion_compliant(wide_df, paper_name, criterion)
            for criterion in fair_criteria
        )
        criteria_counts.append(met_count)

    plot_df = wide_df.copy()
    plot_df["badge_level"] = badge_levels.values
    plot_df["criteria_met"] = criteria_counts

    grouped_counts = []
    for badge_level in BADGE_LEVELS:
        badge_counts = plot_df.loc[plot_df["badge_level"] == badge_level, "criteria_met"]
        grouped_counts.append(badge_counts.to_numpy())

    means = []
    for values in grouped_counts:
        if len(values) == 0:
            means.append(0.0)
        else:
            means.append(float(values.mean()))

    fig, ax = plt.subplots(figsize=(14, 7))
    positions = np.arange(1, len(BADGE_LEVELS) + 1)
    non_empty = [(idx, vals) for idx, vals in enumerate(grouped_counts) if len(vals) > 0]

    if non_empty:
        violin_positions = [positions[idx] for idx, _ in non_empty]
        violin_data = [vals for _, vals in non_empty]
        violin = ax.violinplot(
            violin_data,
            positions=violin_positions,
            widths=0.75,
            showmeans=False,
            showmedians=True,
            showextrema=False,
        )

        for body, (idx, _) in zip(violin["bodies"], non_empty):
            body.set_facecolor(BADGE_CASCADE_COLORS[idx])
            body.set_edgecolor("black")
            body.set_alpha(0.8)
        violin["cmedians"].set_color("black")
        violin["cmedians"].set_linewidth(1.5)

    valid_positions = [positions[idx] for idx, vals in enumerate(grouped_counts) if len(vals) > 0]
    valid_means = [means[idx] for idx, vals in enumerate(grouped_counts) if len(vals) > 0]
    if valid_positions:
        ax.scatter(
            valid_positions,
            valid_means,
            marker="o",
            color="black",
            s=30,
            zorder=5,
            label="Mean",
        )

        for xpos, mean_value in zip(valid_positions, valid_means):
            ax.text(
                xpos,
                mean_value-0.7,
                f"{mean_value:.1f}",
                ha="center",
                va="bottom",
                fontsize=11,
                fontweight='bold'
            )

    ax.set_xlabel("Highest ACM Badge Awarded", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_ylabel("FAIR criteria met per paper", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_xticks(positions)
    ax.set_xticklabels(BADGE_LEVELS, ha='center', fontsize=FONTSIZE_LABELS)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=FONTSIZE_LABELS)
    
    y_max = max((np.max(vals) for vals in grouped_counts if len(vals) > 0), default=1)
    ax.set_ylim(0, y_max * 1.15)

    legend_handles = [
        Line2D([0], [0], color="black", linewidth=1.5, label="Median"),
        Line2D([0], [0], marker="o", color="black", linestyle="None", markersize=6, label="Mean"),
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=FONTSIZE_LEGEND, frameon=True)

    fig.tight_layout()
    save_plot(fig, title="fair_criteria_by_badge")
    plt.show()


def main(df_first_pass=None, df_second_pass=None, df_optimistic=None):
    """
    Generate ACM badge cascade plots.
    
    Args:
        df_first_pass: DataFrame with first-pass FAIR evaluation results (optional).
        df_second_pass: DataFrame with second-pass FAIR evaluation results (optional).
        df_optimistic: DataFrame with optimistic merged FAIR evaluation results (optional).
    """
    if df_first_pass is not None:
        print("Generating ACM badge cascade plots...")
        plot_acm_badge_cascade(df_first_pass)
        print("Generating FAIR criteria by badge plot...")
        plot_fair_criteria_whisker_by_badge(df_first_pass)


if __name__ == '__main__':
    main()
