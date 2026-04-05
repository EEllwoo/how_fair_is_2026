import pandas as pd
from plotnine import ggplot, aes, geom_col, geom_text
import os

def get_repo_stats(file):
    """
    A function that extracts artefact repositories from a single results file
    """
    df = pd.read_csv(file)
    counts = {
        "zenodo_only": 0,
        "github_only": 0,
        "figshare_only": 0,
        "zenodo_and_github": 0,
        "figshare_and_github": 0,
        "unavailable": 0
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
            counts['zenodo_and_github'] += 1
        elif ('figshare' in repository_links or 'figshare' in doi) and ('github' in repository_links or 'github' in github_link):
            counts['figshare_and_github'] += 1
        elif ('zenodo' in repository_links or 'zenodo' in doi):
            counts['zenodo_only'] += 1
        elif ('figshare' in repository_links or 'figshare' in doi):
            counts['figshare_only'] += 1
        elif 'github' in repository_links or 'github' in github_link:
            counts['github_only'] += 1
        else:
            counts['unavailable'] += 1

    return counts

def plot_graph(dict):
    """
    A function to plot the information from get_repo_stats
    """
    # ggplot likes dataframes
    df = pd.DataFrame(list(dict.items()), columns=['Repository Service', 'Count'])
    plot = ggplot(df) + aes(x="Repository Service", y="Count") + geom_col() + geom_text(aes(label='Count'), va='bottom')
    plot.save("graphs/repos.png", width=8, height=6, dpi=300)

if __name__ == "__main__":
    dir = "results/raw"
    results = [
        os.path.join(dir, f)
        for f in os.listdir(dir)
        if f.endswith(".csv")
    ]
    first_pass = results[0]
    second_pass = results[1]

    first_pass_stats = get_repo_stats(first_pass)
    second_pass_stats = get_repo_stats(second_pass)

    print(f"First pass: {first_pass_stats}")
    print(f"Second pass: {second_pass_stats}")

    plot_graph(first_pass_stats)