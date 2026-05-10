"""
This file collects and plots how many of the reviewed papers we found had artefacts we could find.
Note that papers which did not produce artefacts were not scored negatively here, only papers that
did produce software artefacts but that were not accessible to us for whatever reason.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os
import shutil
from pathlib import Path
from plotting_scripts.palette import PASS_COLORS, get_pgf_rc

def _to_dataframe(data_source):
    """Return a DataFrame from DataFrame input or CSV path."""
    if isinstance(data_source, pd.DataFrame):
        return data_source.copy()
    return pd.read_csv(data_source)


def get_availability_stats(data_source):
    """
    A function that takes the csv as input and counts the number of available and unavailable artefacts

    Args:
        data_source (str | DataFrame): Path to CSV file or in-memory DataFrame.

    Returns:
        dict: a dictionary of counts for artefact availability.
    """
    df = _to_dataframe(data_source)

    availability_count = 0
    unavailability_count = 0
    no_artefact_count = 0
    for _, row in df.iterrows():
        # We want to distinguish between artefact unavailable and papers that do not have an associated artefact
        artefact_unavailable = row['F1. Software is assigned a globally unique and persistent identifier (DOI)'] == 'Artefact Unavailable'
        tool = row['Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?'] == 'Yes'
        if artefact_unavailable:
            unavailability_count += 1
        elif tool:
            availability_count += 1
        else:
            no_artefact_count += 1

    return {
        "Available": availability_count,
        "Unavailable": unavailability_count,
        "No Artefact": no_artefact_count
    }

def plot_graph(stats1, stats2=None, filename='', title='', label1='First Pass', label2='Second Pass'):
    """
    Plot grouped bar charts for two availability statistics dictionaries and save it to a PNG.

    Args:
        stats1 (dict): Counts for the first pass.
        stats2 (dict): Counts for the second pass.
        filename (str): Output filename.
        title (str): Chart title.
        label1 (str): First pass legend label.
        label2 (str): Second pass legend label.
    """
    plt.rcParams.update({
        "figure.figsize": (3.5, 2.5),  # Set exact size
        "font.size": 8,                # Match paper caption size
        "axes.labelsize": 9,
        "legend.fontsize": 7,
        "savefig.bbox": 'tight',       # Removes wasted white space
        "lines.linewidth": 1.2
    })
    plt.style.use('ggplot')
    stats2 = stats2 or {}
    categories = sorted(set(stats1) | set(stats2), key=lambda item: max(stats1.get(item, 0), stats2.get(item, 0)), reverse=True)
    values1 = [stats1.get(category, 0) for category in categories]
    values2 = [stats2.get(category, 0) for category in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    if stats2:
        bars1 = ax.bar(x - width / 2, values1, width, label=label1, color=PASS_COLORS[0], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x + width / 2, values2, width, label=label2, color=PASS_COLORS[1], edgecolor='black', linewidth=0.5)
        all_bars = list(bars1) + list(bars2)
    else:
        bars1 = ax.bar(x, values1, width=0.6, label=label1, color=PASS_COLORS[0], edgecolor='black', linewidth=0.5)
        all_bars = list(bars1)

    ax.set_xlabel('Availability')
    ax.xaxis.labelpad = 12
    ax.set_ylabel('Count')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.tick_params(axis='x', pad=6)
    ax.legend()

    for bar in all_bars:
        height = bar.get_height()
        ax.annotate(
            f'{int(height)}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center',
            va='bottom'
        )

    fig.tight_layout()
    graphs_dir = Path("graphs")
    pgf_dir = graphs_dir / "pgf"
    graphs_dir.mkdir(exist_ok=True)
    pgf_dir.mkdir(exist_ok=True)

    png_output_path = graphs_dir / f"{filename}.png"
    pgf_output_path = pgf_dir / f"{filename}.pgf"

    fig.savefig(png_output_path, dpi=300)
    tex_candidates = ("pdflatex", "lualatex", "xelatex")
    selected_tex = next((tex for tex in tex_candidates if shutil.which(tex)), None)
    if selected_tex is None:
        print("Warning: PGF export skipped (no LaTeX engine found: xelatex/lualatex/pdflatex)")
    else:
        try:
            with mpl.rc_context(get_pgf_rc(selected_tex)):
                fig.savefig(pgf_output_path, backend="pgf")
        except Exception as exc:
            print(f"Warning: failed to save PGF plot to {pgf_output_path}: {exc}")

def availability_main(data_source=None):
    """
    The main function for this script
    """
    if data_source is not None:
        optimistic_stats = get_availability_stats(data_source)
        print(f"Optimistic: {optimistic_stats}")
        plot_graph(
            optimistic_stats,
            None,
            "availability_optimistic",
            "Availability of Artefacts: Optimistic",
            label1='Optimistic',
        )
        return

    dir = "results/"
    results = [
        os.path.join(dir, f)
        for f in os.listdir(dir)
        if f.endswith("_fixed.csv")
    ]
    first_pass = results[0]
    second_pass = results[1]

    first_pass_stats = get_availability_stats(first_pass)
    second_pass_stats = get_availability_stats(second_pass)

    print(f"First pass: {first_pass_stats}")
    print(f"Second pass: {second_pass_stats}")

    plot_graph(
        first_pass_stats,
        second_pass_stats,
        "availability_comparison",
        "Availability of Artefacts: First Pass vs Second Pass",
        label1='First Pass',
        label2='Second Pass',
    )

if __name__ == '__main__':
    availability_main()
