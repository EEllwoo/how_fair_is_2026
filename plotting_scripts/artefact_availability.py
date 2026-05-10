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
from plotting_scripts.fair_letter_compliance import save_plot

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

def plot_graph(stats1, stats2=None, stats3=None, title='', label1='First Pass', label2='Second Pass', label3='Optimistic'):
    """
    Plot grouped bar charts for availability statistics dictionaries and save it to a PNG.

    Args:
        stats1 (dict): Counts for the first pass.
        stats2 (dict): Counts for the second pass (optional).
        stats3 (dict): Counts for the optimistic dataset (optional).
        title (str): Output filename (will be sanitized).
        label1 (str): First pass legend label.
        label2 (str): Second pass legend label.
        label3 (str): Optimistic legend label.
    """
    plt.style.use('ggplot')
    stats2 = stats2 or {}
    stats3 = stats3 or {}
    categories = sorted(set(stats1) | set(stats2) | set(stats3), key=lambda item: max(stats1.get(item, 0), stats2.get(item, 0), stats3.get(item, 0)), reverse=True)
    values1 = [stats1.get(category, 0) for category in categories]
    values2 = [stats2.get(category, 0) for category in categories]
    values3 = [stats3.get(category, 0) for category in categories]

    x = np.arange(len(categories))
    width = 0.25 if (stats2 and stats3) else (0.35 if stats2 else 0.6)

    fig, ax = plt.subplots(figsize=(12, 6))
    if stats2 and stats3:
        bars1 = ax.bar(x - width, values1, width, label=label1, color=PASS_COLORS[0], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x, values2, width, label=label2, color=PASS_COLORS[1], edgecolor='black', linewidth=0.5)
        bars3 = ax.bar(x + width, values3, width, label=label3, color='#4472C4', edgecolor='black', linewidth=0.5)
        all_bars = list(bars1) + list(bars2) + list(bars3)
    elif stats2:
        bars1 = ax.bar(x - width / 2, values1, width, label=label1, color=PASS_COLORS[0], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x + width / 2, values2, width, label=label2, color=PASS_COLORS[1], edgecolor='black', linewidth=0.5)
        all_bars = list(bars1) + list(bars2)
    else:
        bars1 = ax.bar(x, values1, width=0.6, label=label1, color=PASS_COLORS[0], edgecolor='black', linewidth=0.5)
        all_bars = list(bars1)

    ax.set_xlabel('Availability', fontsize=12, fontweight='bold')
    ax.xaxis.labelpad = 12
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
    ax.tick_params(axis='x', pad=6)
    ax.legend(fontsize=11)

    for bar in all_bars:
        height = bar.get_height()
        ax.annotate(
            f'{int(height)}',
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center',
            va='bottom',
            fontweight='bold'
        )

    fig.tight_layout()
    save_plot(fig, title=title)

def availability_main(first_pass_df=None, second_pass_df=None, optimistic_df=None):
    """
    Generate artifact availability plots.
    
    Args:
        first_pass_df: DataFrame with first-pass FAIR evaluation results (optional).
        second_pass_df: DataFrame with second-pass FAIR evaluation results (optional).
        optimistic_df: DataFrame with optimistic merged FAIR evaluation results (optional).
                       If all None, loads from results/ directory.
    """
    if first_pass_df is not None:
        first_pass_stats = get_availability_stats(first_pass_df)
        print(f"First pass: {first_pass_stats}")
        
        if second_pass_df is not None:
            second_pass_stats = get_availability_stats(second_pass_df)
            print(f"Second pass: {second_pass_stats}")
            
            if optimistic_df is not None:
                optimistic_stats = get_availability_stats(optimistic_df)
                print(f"Optimistic: {optimistic_stats}")
                
                plot_graph(
                    first_pass_stats,
                    second_pass_stats,
                    optimistic_stats,
                    "availability_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                    label3='Optimistic',
                )
            else:
                plot_graph(
                    first_pass_stats,
                    second_pass_stats,
                    None,
                    "availability_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                )
        else:
            plot_graph(
                first_pass_stats,
                None,
                None,
                "availability_first_pass",
                label1='First Pass',
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
        label1='First Pass',
        label2='Second Pass',
    )

if __name__ == '__main__':
    availability_main()
