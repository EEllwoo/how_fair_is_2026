import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import re
import shutil
from pathlib import Path


def get_repo_stats(file):
    """
    A function that extracts artefact repositories from a single results file

    Args:
        file (str): Path to CSV file.

    Returns:
        dict: a dictionary of counts for each repository service.
    """
    df = pd.read_csv(file)
    counts = {
        "Zenodo Only": 0,
        "GitHub Only": 0,
        "Figshare Only": 0,
        "Zenodo and GitHub": 0,
        "Figshare and GitHub": 0,
        "Anonymous GitHub Only": 0,
        "Artefact Unavailable": 0,
        "No Artefact": 0,
        "Google Sites": 0,
        "Other": 0
    }
    for _, row in df.iterrows():
        repository_links = row['Link to artefact repository (Github, Zenodo, Figshare etc)']
        github_link  = row['Please input any links to GitHub if available']
        doi = row['If F1 is met, please input the DOI of the latest version']
        tool = row['Are any software artefacts/tools/scripts mentioned in and used in the process of gathering results for the report?'] == 'Yes'
        tool_unavailable = row['F1. Software is assigned a globally unique and persistent identifier (DOI)'] == 'Artefact Unavailable'

        if pd.isnull(repository_links):
            repository_links = []
        if pd.isnull(github_link):
            github_link = []
        if pd.isnull(doi):
            doi = []

        if ('zenodo' in repository_links or 'zenodo' in doi) and ('github' in repository_links or 'github' in github_link):
            counts['Zenodo and GitHub'] += 1
        elif ('figshare' in repository_links or 'figshare' in doi) and ('github' in repository_links or 'github' in github_link):
            counts['Figshare and GitHub'] += 1
        elif ('zenodo' in repository_links or 'zenodo' in doi):
            counts['Zenodo Only'] += 1
        elif ('figshare' in repository_links or 'figshare' in doi):
            counts['Figshare Only'] += 1
        elif 'github' in repository_links or 'github' in github_link:
            counts['GitHub Only'] += 1
        elif 'anonymous' in repository_links or 'anonymous' in github_link:
            counts["Anonymous GitHub Only"] += 1
        elif not tool:
            counts['No Artefact'] += 1
        elif 'sites' in repository_links:
            counts['Google Sites'] += 1
        elif tool_unavailable or (repository_links == [] and github_link == [] and doi == []):
            counts['Artefact Unavailable'] += 1
        else:
            counts['Other'] += 1
    return counts

def plot_graph(first_pass_stats, second_pass_stats):
    """
    Plot first and second pass repository service counts side by side and save to PNG.

    Args:
        first_pass_stats (dict): Repository service counts for the first pass.
        second_pass_stats (dict): Repository service counts for the second pass.
    """
    plt.style.use('ggplot')
    categories = sorted(
        set(first_pass_stats) | set(second_pass_stats),
        key=lambda category: max(first_pass_stats.get(category, 0), second_pass_stats.get(category, 0)),
        reverse=True
    )
    first_counts = [first_pass_stats.get(category, 0) for category in categories]
    second_counts = [second_pass_stats.get(category, 0) for category in categories]
    x_positions = range(len(categories))
    bar_width = 0.4

    fig, ax = plt.subplots(figsize=(14, 7))
    first_bars = ax.bar(
        [position - bar_width / 2 for position in x_positions],
        first_counts,
        width=bar_width,
        color='#4ECDC4',
        edgecolor='black',
        linewidth=0.5,
        label='First Pass'
    )
    second_bars = ax.bar(
        [position + bar_width / 2 for position in x_positions],
        second_counts,
        width=bar_width,
        color='#FF6B6B',
        edgecolor='black',
        linewidth=0.5,
        label='Second Pass'
    )

    ax.set_xlabel('Repository Service')
    ax.set_ylabel('Count')
    ax.set_title('Repository Service Counts by Pass')
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()

    for bars in (first_bars, second_bars):
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
    title = ax.get_title()
    safe_title = re.sub(r"[^A-Za-z0-9]+", "_", title.strip()).strip("_").lower() or "plot"
    png_output_path = graphs_dir / f"{safe_title}.png"
    pgf_output_path = pgf_dir / f"{safe_title}.pgf"

    fig.savefig(png_output_path, dpi=300, bbox_inches="tight")
    tex_candidates = ("pdflatex", "lualatex", "xelatex")
    selected_tex = next((tex for tex in tex_candidates if shutil.which(tex)), None)
    if selected_tex is None:
        print("Warning: PGF export skipped (no LaTeX engine found: xelatex/lualatex/pdflatex)")
    else:
        original_tex = mpl.rcParams.get("pgf.texsystem", "xelatex")
        try:
            mpl.rcParams["pgf.texsystem"] = selected_tex
            fig.savefig(pgf_output_path, bbox_inches="tight")
        except Exception as exc:
            print(f"Warning: failed to save PGF plot to {pgf_output_path}: {exc}")
        finally:
            mpl.rcParams["pgf.texsystem"] = original_tex

def repo_stats_main():
    dir = "results/"
    results = [
        os.path.join(dir, f)
        for f in os.listdir(dir)
        if f.endswith("_fixed.csv")
    ]
    first_pass = results[0]
    second_pass = results[1]

    first_pass_stats = get_repo_stats(first_pass)
    second_pass_stats = get_repo_stats(second_pass)

    print(f"First pass: {first_pass_stats}")
    print(f"Second pass: {second_pass_stats}")

    plot_graph(first_pass_stats, second_pass_stats)

if __name__ == '__main__':
    repo_stats_main()