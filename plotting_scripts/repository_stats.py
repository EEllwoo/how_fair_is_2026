"""
This file collects and plots some information on our results
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import shutil
from pathlib import Path


def get_repo_stats_available(file):
    """
    A function that extracts artefact repositories from a single results file.

    Since some papers had associated repository sites but the artefact itself was unavailable e.g. anonymous GitHub 
    expiration. We have split the counts into available and unavailable

    Args:
        file (str): Path to CSV file.

    Returns:
        dict: a dictionary of counts_available and counts_unavailable for each repository service.
    """
    df = pd.read_csv(file)
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

def plot_graph(stats, filename, title):
    """
    A void function to plot the information from get_repo_stats and save it to a png

    Args:
        stats (dict): A dictionary of the counts_available of each repository service
        filename (str): Filename for the graph
    """
    plt.style.use('ggplot')
    sorted_items = sorted(stats.items(), key=lambda item: item[1], reverse=True)
    categories = [item[0] for item in sorted_items]
    counts_available = [item[1] for item in sorted_items]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#B0E0E6', '#E0BBE4', '#F7CAC9', '#E8F1D4', '#FFD1DC']

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(categories, counts_available, color=colors[:len(categories)], edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Repository Service')
    ax.set_ylabel('Count')
    ax.set_title(title)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha='right')

    for bar in bars:
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
        original_tex = mpl.rcParams.get("pgf.texsystem", "xelatex")
        try:
            mpl.rcParams["pgf.texsystem"] = selected_tex
            fig.savefig(pgf_output_path)
        except Exception as exc:
            print(f"Warning: failed to save PGF plot to {pgf_output_path}: {exc}")
        finally:
            mpl.rcParams["pgf.texsystem"] = original_tex

def repo_stats_main():
    """
    The main function for this script
    """
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

    plot_graph(first_pass_available, "repos_first_pass_available", "Repository Service Counts (from available artefacts) (first pass)")
    plot_graph(second_pass_available, "repos_second_pass_available", "Repository Service Counts (from available artefacts) (second pass)")
    plot_graph(first_pass_unavailable, "repos_first_pass_unavailable", "Repository Service Counts (from unavailable artefacts) (first pass)")
    plot_graph(second_pass_unavailable, "repos_second_pass_unavailable", "Repository Service Counts (from unavailable artefacts) (second pass)")

if __name__ == '__main__':
    repo_stats_main()