"""
This file collects and plots how many of the reviewed papers we found had artefacts we could find.
Note that papers which did not produce artefacts were not scored negatively here, only papers that
did produce software artefacts but that were not accessible to us for whatever reason.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

def get_availability_stats(file):
    """
    A function that takes the csv as input and counts the number of available and unavailable artefacts

    Args:
        file (str): Path to CSV file.

    Returns:
        dict: a dictionary of counts for artefact availability.
    """
    df = pd.read_csv(file)

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

def plot_graph(dict, filename):
    """
    A function that plots the graph given the dictionary from get_availability_stats

    Args:
        dict (dict): Dictionary of counts
        filename (str): name for the file
    """

    plt.style.use('ggplot')
    categories = dict.keys()
    counts = dict.values()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(categories, counts, edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Availability')
    ax.set_ylabel('Count')
    ax.set_title('Availability of Artefacts')
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories)

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
    fig.savefig(f"graphs/{filename}.png", dpi=300)

def availability_main():
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

    first_pass_stats = get_availability_stats(first_pass)
    second_pass_stats = get_availability_stats(second_pass)

    print(f"First pass: {first_pass_stats}")
    print(f"Second pass: {second_pass_stats}")

    plot_graph(first_pass_stats, "availability_first_pass")
    plot_graph(second_pass_stats, "availability_second_pass")

if __name__ == '__main__':
    availability_main()
