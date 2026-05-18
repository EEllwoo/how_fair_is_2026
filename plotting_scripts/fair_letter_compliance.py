"""Plot overall FAIR compliance by letter."""

import re
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch
from plotting_scripts.FAIR_compliance import calculate_all_letter_compliance_rates
from processing_scripts.pre_process import scleaned_pandas
from plotting_scripts.palette import FAIR_LETTER_COLORS, get_pgf_rc, FONTSIZE_AXES, FONTSIZE_LABELS, FONTSIZE_TEXT


def save_plot(fig, title=None, graphs_dir=None, tex_engine=None):
    """Save a matplotlib figure to PNG and optionally PGF in separate folders."""
    if graphs_dir is None:
        graphs_dir = Path("graphs")
    graphs_dir.mkdir(exist_ok=True)
    pgf_dir = graphs_dir / "pgf"
    pgf_dir.mkdir(exist_ok=True)

    if title is None:
        if fig._suptitle is not None:
            title = fig._suptitle.get_text()
        elif fig.axes:
            title = fig.axes[0].get_title()
        else:
            title = "plot"

    safe_title = re.sub(r"[^A-Za-z0-9]+", "_", title.strip()).strip("_").lower() or "plot"
    png_output_path = graphs_dir / f"{safe_title}.png"
    pgf_output_path = pgf_dir / f"{safe_title}.pgf"

    fig.savefig(png_output_path, dpi=300, bbox_inches="tight")
    print(f"Saved PNG plot to {png_output_path}")

    # Detect a TeX engine if not supplied by the caller.
    if tex_engine is None:
        tex_engine = next(
            (t for t in ("pdflatex", "lualatex", "xelatex") if shutil.which(t)), None
        )

    if tex_engine:
        pgf_rc = get_pgf_rc(tex_engine)
        with mpl.rc_context(pgf_rc):
            fig.savefig(pgf_output_path, backend="pgf", bbox_inches="tight")
        print(f"Saved PGF plot to {pgf_output_path}")
    else:
        print("PGF export skipped: no TeX engine found (install MiKTeX or TeX Live)")


def plot_fair_letter_compliance(first_pass_df, second_pass_df=None, optimistic_df=None):
    """
    Generate bar chart showing overall FAIR compliance rates by letter (F, A, I, R).
    If multiple passes are supplied, display grouped bars side-by-side.
    
    Args:
        first_pass_df: DataFrame with first-pass FAIR evaluation results
        second_pass_df: Optional DataFrame with second-pass FAIR evaluation results
        optimistic_df: Optional DataFrame with optimistic merged FAIR evaluation results
    """
    first_pass_compliance = calculate_all_letter_compliance_rates(first_pass_df)
    letters = list(first_pass_compliance.keys())
    letter_colors = FAIR_LETTER_COLORS

    fig, ax = plt.subplots(figsize=(12, 6))

    if second_pass_df is None and optimistic_df is None:
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
                fontsize=FONTSIZE_LABELS,
            )
    elif optimistic_df is None:
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
                    fontsize=FONTSIZE_TEXT,
                )
    else:
        second_pass_compliance = calculate_all_letter_compliance_rates(second_pass_df)
        optimistic_compliance = calculate_all_letter_compliance_rates(optimistic_df)
        first_rates = [first_pass_compliance[letter] for letter in letters]
        second_rates = [second_pass_compliance[letter] for letter in letters]
        optimistic_rates = [optimistic_compliance[letter] for letter in letters]
        x = np.arange(len(letters))
        width = 0.26

        first_bars = ax.bar(
            x - width,
            first_rates,
            width,
            label="First pass",
            color=letter_colors,
            alpha=0.85,
            edgecolor="black",
        )
        second_bars = ax.bar(
            x,
            second_rates,
            width,
            label="Second pass",
            color=letter_colors,
            alpha=0.55,
            hatch="//",
            edgecolor="black",
        )
        optimistic_bars = ax.bar(
            x + width,
            optimistic_rates,
            width,
            label="Optimistic",
            color=letter_colors,
            alpha=0.35,
            hatch="xx",
            edgecolor="black",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(letters)
        ax.legend(
            handles=[
                Patch(facecolor="white", edgecolor="black", label="First pass"),
                Patch(facecolor="white", edgecolor="black", hatch="//", label="Second pass"),
                Patch(facecolor="white", edgecolor="black", hatch="xx", label="Optimistic"),
            ],
            title="Pass",
        )

        for bar_group in (first_bars, second_bars, optimistic_bars):
            for bar in bar_group:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=FONTSIZE_TEXT,
                )

    ax.set_ylabel("Compliance Rate (%)", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_xlabel("FAIR Letter", fontsize=FONTSIZE_AXES, fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=FONTSIZE_LABELS)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=FONTSIZE_LABELS)
    ax.set_ylim(0, 100)

    plt.style.use("ggplot")
    plt.tight_layout()
    save_plot(fig, title="fair_letter_compliance")
    plt.show()


def main(df_first_pass=None, df_second_pass=None, df_optimistic=None):
    """
    Generate FAIR letter compliance plots.
    
    Args:
        df_first_pass: DataFrame with first-pass FAIR evaluation results (optional).
        df_second_pass: DataFrame with second-pass FAIR evaluation results (optional).
        df_optimistic: DataFrame with optimistic merged FAIR evaluation results (optional).
    """
    if df_first_pass is not None:
        print("Generating FAIR letter compliance plot...")
        plot_fair_letter_compliance(df_first_pass, df_second_pass, df_optimistic)


if __name__ == '__main__':
    main()
