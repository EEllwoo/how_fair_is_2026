"""Plot overall FAIR compliance by letter."""

import re
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from plotting_scripts.FAIR_compliance import calculate_all_letter_compliance_rates
from processing_scripts.pre_process import scleaned_pandas


def save_plot(fig, title=None, graphs_dir=None):
    """Save a matplotlib figure to a PNG file."""
    if graphs_dir is None:
        graphs_dir = Path("graphs")
    graphs_dir.mkdir(exist_ok=True)
    
    if title is None:
        if fig._suptitle is not None:
            title = fig._suptitle.get_text()
        elif fig.axes:
            title = fig.axes[0].get_title()
        else:
            title = "plot"

    safe_title = re.sub(r"[^A-Za-z0-9]+", "_", title.strip()).strip("_").lower() or "plot"
    output_path = graphs_dir / f"{safe_title}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved plot to {output_path}")


def plot_fair_letter_compliance(first_pass_df, second_pass_df=None):
    """
    Generate bar chart showing overall FAIR compliance rates by letter (F, A, I, R).
    If both passes are supplied, display grouped bars side-by-side.
    
    Args:
        first_pass_df: DataFrame with first-pass FAIR evaluation results
        second_pass_df: Optional DataFrame with second-pass FAIR evaluation results
    """
    first_pass_compliance = calculate_all_letter_compliance_rates(first_pass_df)
    letters = list(first_pass_compliance.keys())
    letter_colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"]

    fig, ax = plt.subplots(figsize=(12, 6))

    if second_pass_df is None:
        rates = list(first_pass_compliance.values())
        bars = ax.bar(
            letters,
            rates,
            color=letter_colors,
            alpha=0.8,
            edgecolor="black",
        )

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.1f}%",
                ha="center",
                va="bottom",
                fontsize=10,
            )
    else:
        second_pass_compliance = calculate_all_letter_compliance_rates(second_pass_df)
        first_rates = [first_pass_compliance[letter] for letter in letters]
        second_rates = [second_pass_compliance[letter] for letter in letters]
        x = np.arange(len(letters))
        width = 0.36

        first_bars = ax.bar(
            x - width / 2,
            first_rates,
            width,
            label="First pass",
            color=letter_colors,
            alpha=0.85,
            edgecolor="black",
        )
        second_bars = ax.bar(
            x + width / 2,
            second_rates,
            width,
            label="Second pass",
            color=letter_colors,
            alpha=0.45,
            hatch="//",
            edgecolor="black",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(letters)
        ax.legend(
            handles=[
                Patch(facecolor="white", edgecolor="black", label="First pass"),
                Patch(facecolor="white", edgecolor="black", hatch="//", label="Second pass"),
            ],
            title="Pass",
        )

        for bar_group in (first_bars, second_bars):
            for bar in bar_group:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    ax.set_ylabel("Compliance Rate (%)", fontsize=12)
    ax.set_xlabel("FAIR Letter", fontsize=12)
    ax.set_title("Overall FAIR Compliance by Letter", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 100)

    plt.style.use("ggplot")
    plt.tight_layout()
    save_plot(fig)
    plt.show()
