"""Plot overall FAIR compliance by letter."""

import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
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


def plot_fair_letter_compliance(df):
    """
    Generate bar chart showing overall FAIR compliance rates by letter (F, A, I, R).
    
    Args:
        df: DataFrame with FAIR evaluation results
    """
    # Plot full FAIR compliance by letter
    compliance_by_letter = calculate_all_letter_compliance_rates(df)

    letters = list(compliance_by_letter.keys())
    rates = list(compliance_by_letter.values())

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(
        letters,
        rates,
        color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"],
        alpha=0.8,
        edgecolor="black",
    )
    ax.set_ylabel("Compliance Rate (%)", fontsize=12)
    ax.set_xlabel("FAIR Letter", fontsize=12)
    ax.set_title("Overall FAIR Compliance by Letter", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 100)

    # Add value labels on bars
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

    plt.style.use("ggplot")
    plt.tight_layout()
    save_plot(fig)
    plt.show()
