import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os


def get_repo_stats(file):
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

def plot_graph(stats1, stats2, filename, title, label1='First Pass', label2='Second Pass'):
    """
    Plot grouped bar charts for two repository statistics dictionaries and save the result.

    Args:
        stats1 (dict): Counts for the first pass.
        stats2 (dict): Counts for the second pass.
        filename (str): Filename for the graph output.
        title (str): Title for the chart.
        label1 (str): Label for the first set of bars.
        label2 (str): Label for the second set of bars.
    """
    plt.style.use('ggplot')
    categories = sorted(
        set(stats1) | set(stats2),
        key=lambda item: max(stats1.get(item, 0), stats2.get(item, 0)),
        reverse=True,
    )
    values1 = [stats1.get(category, 0) for category in categories]
    values2 = [stats2.get(category, 0) for category in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 7))
    bars1 = ax.bar(x - width / 2, values1, width, label=label1, color='#4ECDC4', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width / 2, values2, width, label=label2, color='#FF6B6B', edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Repository Service')
    ax.set_ylabel('Count')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=45, ha='right')
    ax.legend()

    for bar in list(bars1) + list(bars2):
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
    fig.savefig(f"graphs/{filename}.png", dpi=300)

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

    first_pass_available, first_pass_unavailable = get_repo_stats(first_pass)
    second_pass_available, second_pass_unavailable = get_repo_stats(second_pass)

    print(f"First pass (out of available papers): {first_pass_available}")
    print(f"First pass (out of unavailable papers): {first_pass_unavailable}")
    print(f"Second pass (out of available papers): {second_pass_available}")
    print(f"Second pass (out of unavailable papers): {second_pass_unavailable}")

    plot_graph(
        first_pass_available,
        second_pass_available,
        "repos_available_comparison",
        "Repository Service Counts (available artefacts): First Pass vs Second Pass",
        label1='First Pass',
        label2='Second Pass',
    )
    plot_graph(
        first_pass_unavailable,
        second_pass_unavailable,
        "repos_unavailable_comparison",
        "Repository Service Counts (unavailable artefacts): First Pass vs Second Pass",
        label1='First Pass',
        label2='Second Pass',
    )

if __name__ == '__main__':
    repo_stats_main()