import pandas as pd
from plotnine import ggplot, aes, geom_col, geom_text
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
        "Unavailable": 0
    }
    for _, row in df.iterrows():
        repository_links = row['Link to artefact repository (Github, Zenodo, Figshare etc)']
        github_link  = row['Please input any links to GitHub if available']
        doi = row['If F1 is met, please input the DOI of the latest version']

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
        else:
            counts['Unavailable'] += 1
    return counts

def plot_graph(dict):
    """
    A void function to plot the information from get_repo_stats and save it to a png

    Args:
        dict (dict): A dictionary of the counts of each repository services
    """
    # ggplot likes dataframes
    df = pd.DataFrame(list(dict.items()), columns=['Repository Service', 'Count'])
    plot = ggplot(df) + aes(x="Repository Service", y="Count") + geom_col() + geom_text(aes(label='Count'), va='bottom')
    plot.save("graphs/repos.png", width=12, height=6, dpi=300)

if __name__ == "__main__":
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

    plot_graph(first_pass_stats)