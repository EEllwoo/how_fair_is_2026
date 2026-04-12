import pandas as pd
import matplotlib.pyplot as plt
import os


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

def plot_graph(stats):
    """
    A void function to plot the information from get_repo_stats and save it to a png

    Args:
        stats (dict): A dictionary of the counts of each repository service
    """
    plt.style.use('ggplot')
    sorted_items = sorted(stats.items(), key=lambda item: item[1], reverse=True)
    categories = [item[0] for item in sorted_items]
    counts = [item[1] for item in sorted_items]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#B0E0E6', '#E0BBE4', '#F7CAC9', '#E8F1D4', '#FFD1DC']

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(categories, counts, color=colors[:len(categories)], edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Repository Service')
    ax.set_ylabel('Count')
    ax.set_title('Repository Service Counts')
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
    fig.savefig("graphs/repos.png", dpi=300)

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

    # Use first pass as we have all papers
    plot_graph(first_pass_stats)