"""
This file collects and plots some information on our results
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import shutil
import numpy as np
import re
from pathlib import Path
from plotting_scripts.palette import PASS_COLORS, get_pgf_rc
from plotting_scripts.fair_letter_compliance import save_plot


def _to_dataframe(data_source):
    """Return a DataFrame from DataFrame input or CSV path."""
    if isinstance(data_source, pd.DataFrame):
        return data_source.copy()
    return pd.read_csv(data_source)


def get_repo_stats_available(data_source):
    """
    A function that extracts artefact repositories from a single results file.

    Since some papers had associated repository sites but the artefact itself was unavailable e.g. anonymous GitHub 
    expiration. We have split the counts into available and unavailable

    Args:
        data_source (str | DataFrame): Path to CSV file or in-memory DataFrame.

    Returns:
        dict: a dictionary of counts_available and counts_unavailable for each repository service.
    """
    df = _to_dataframe(data_source)
    counts_available = {
        "Zenodo Only": 0,
        "GitHub Only": 0,
        "Figshare Only": 0,
        "Zenodo and GitHub": 0,
        "Figshare and GitHub": 0,
        "Anonymous GitHub Only": 0,
        "Google Sites": 0,
        "Other": 0
    }

    counts_unavailable = {
        "Zenodo Only": 0,
        "GitHub Only": 0,
        "Figshare Only": 0,
        "Zenodo and GitHub": 0,
        "Figshare and GitHub": 0,
        "Anonymous GitHub Only": 0,
        "Google Sites": 0,
        "Not Found": 0 # If there were truly no repo sites then we say it was unavailable under the pretense it could not be found
    }
    for _, row in df.iterrows():
        repository_links = row['Link to artefact repository (Github, Zenodo, Figshare etc)']
        github_link  = row['Please input any links to GitHub if available']
        doi = row['If F1 is met, please input the DOI of the latest version']
        tool = row['Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?']
        tool_unavailable = row['F1. Software is assigned a globally unique and persistent identifier (DOI)'] == 'Artefact Unavailable'

        if pd.isnull(repository_links):
            repository_links = []
        if pd.isnull(github_link):
            github_link = []
        if pd.isnull(doi):
            doi = []

        if tool == 'Yes':
            if not tool_unavailable:
                if ('zenodo' in repository_links or 'zenodo' in doi) and ('github' in repository_links or 'github' in github_link):
                    counts_available['Zenodo and GitHub'] += 1
                elif ('figshare' in repository_links or 'figshare' in doi) and ('github' in repository_links or 'github' in github_link):
                    counts_available['Figshare and GitHub'] += 1
                elif ('zenodo' in repository_links or 'zenodo' in doi):
                    counts_available['Zenodo Only'] += 1
                elif ('figshare' in repository_links or 'figshare' in doi):
                    counts_available['Figshare Only'] += 1
                elif 'github' in repository_links or 'github' in github_link:
                    counts_available['GitHub Only'] += 1
                elif 'anonymous' in repository_links or 'anonymous' in github_link:
                    counts_available["Anonymous GitHub Only"] += 1
                elif 'sites' in repository_links:
                    counts_available['Google Sites'] += 1
                else:
                    counts_available['Other'] += 1
            else:
                if ('zenodo' in repository_links or 'zenodo' in doi) and ('github' in repository_links or 'github' in github_link):
                    counts_unavailable['Zenodo and GitHub'] += 1
                elif ('figshare' in repository_links or 'figshare' in doi) and ('github' in repository_links or 'github' in github_link):
                    counts_unavailable['Figshare and GitHub'] += 1
                elif ('zenodo' in repository_links or 'zenodo' in doi):
                    counts_unavailable['Zenodo Only'] += 1
                elif ('figshare' in repository_links or 'figshare' in doi):
                    counts_unavailable['Figshare Only'] += 1
                elif 'github' in repository_links or 'github' in github_link:
                    counts_unavailable['GitHub Only'] += 1
                elif 'anonymous' in repository_links or 'anonymous' in github_link:
                    counts_unavailable["Anonymous GitHub Only"] += 1
                elif 'sites' in repository_links:
                    counts_unavailable['Google Sites'] += 1
                else:
                    counts_unavailable['Not Found'] += 1
        elif tool == 'No':
            pass
    return counts_available, counts_unavailable

def plot_graph(stats1, stats2=None, stats3=None, title='', label1='First Pass', label2='Second Pass', label3='Optimistic'):
    """
    Plot grouped bar charts for repository statistics dictionaries and save the result.

    Args:
        stats1 (dict): Counts for the first pass.
        stats2 (dict): Counts for the second pass (optional).
        stats3 (dict): Counts for the optimistic dataset (optional).
        title (str): Title for the chart (used for filename, not displayed).
        label1 (str): Label for the first set of bars.
        label2 (str): Label for the second set of bars.
        label3 (str): Label for the third set of bars.
    """
    plt.style.use('ggplot')
    stats2 = stats2 or {}
    stats3 = stats3 or {}
    categories = sorted(
        set(stats1) | set(stats2) | set(stats3),
        key=lambda item: max(stats1.get(item, 0), stats2.get(item, 0), stats3.get(item, 0)),
        reverse=True,
    )
    values1 = [stats1.get(category, 0) for category in categories]
    values2 = [stats2.get(category, 0) for category in categories]
    values3 = [stats3.get(category, 0) for category in categories]

    x = np.arange(len(categories))
    width = 0.25 if (stats2 and stats3) else (0.35 if stats2 else 0.6)

    fig, ax = plt.subplots(figsize=(16, 7))
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

    ax.set_xlabel('Repository Service', fontsize=14, fontweight='bold')
    ax.set_ylabel('Count', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=12, fontweight='bold')
    ax.legend(fontsize=12)

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

def repo_stats_main(first_pass_df=None, second_pass_df=None, optimistic_df=None):
    """
    Generate repository statistics plots for FAIR evaluation results.
    
    Args:
        first_pass_df: DataFrame with first-pass FAIR evaluation results (optional).
                       If None, loads from results/ directory.
        second_pass_df: DataFrame with second-pass FAIR evaluation results (optional).
        optimistic_df: DataFrame with optimistic merged FAIR evaluation results (optional).
    """
    if first_pass_df is not None:
        # Generate plots from provided dataframes
        first_pass_available, first_pass_unavailable = get_repo_stats_available(first_pass_df)
        print(f"First pass (available papers): {first_pass_available}")
        print(f"First pass (unavailable papers): {first_pass_unavailable}")
        
        if second_pass_df is not None:
            second_pass_available, second_pass_unavailable = get_repo_stats_available(second_pass_df)
            print(f"Second pass (available papers): {second_pass_available}")
            print(f"Second pass (unavailable papers): {second_pass_unavailable}")
            
            if optimistic_df is not None:
                optimistic_available, optimistic_unavailable = get_repo_stats_available(optimistic_df)
                print(f"Optimistic (available papers): {optimistic_available}")
                print(f"Optimistic (unavailable papers): {optimistic_unavailable}")
                
                plot_graph(
                    first_pass_available,
                    second_pass_available,
                    optimistic_available,
                    "repository_available_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                    label3='Optimistic',
                )
                plot_graph(
                    first_pass_unavailable,
                    second_pass_unavailable,
                    optimistic_unavailable,
                    "repository_unavailable_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                    label3='Optimistic',
                )
            else:
                plot_graph(
                    first_pass_available,
                    second_pass_available,
                    None,
                    "repository_available_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                )
                plot_graph(
                    first_pass_unavailable,
                    second_pass_unavailable,
                    None,
                    "repository_unavailable_comparison",
                    label1='First Pass',
                    label2='Second Pass',
                )
        else:
            plot_graph(
                first_pass_available,
                None,
                None,
                "repository_available_first_pass",
                label1='First Pass',
            )
            plot_graph(
                first_pass_unavailable,
                None,
                None,
                "repository_unavailable_first_pass",
                label1='First Pass',
            )
        return

    # Original behavior: load from results directory
    dir = "results/"
    results = [
        os.path.join(dir, f)
        for f in os.listdir(dir)
        if f.endswith("_fixed.csv")
    ]
    first_pass = results[0]
    second_pass = results[1]

    first_pass_available, first_pass_unavailable = get_repo_stats_available(first_pass)
    second_pass_available, second_pass_unavailable = get_repo_stats_available(second_pass)

    print(f"First pass (out of available papers): {first_pass_available}")
    print(f"First pass (out of unavailable papers): {first_pass_unavailable}")
    print(f"Second pass (out of available papers): {second_pass_available}")
    print(f"Second pass (out of unavailable papers): {second_pass_unavailable}")

    plot_graph(
        first_pass_available,
        second_pass_available,
        "repository_available_comparison",
        label1='First Pass',
        label2='Second Pass',
    )
    plot_graph(
        first_pass_unavailable,
        second_pass_unavailable,
        "repository_unavailable_comparison",
        label1='First Pass',
        label2='Second Pass',
    )

if __name__ == '__main__':
    repo_stats_main()