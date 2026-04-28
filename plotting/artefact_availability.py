import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
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

def plot_graph(stats1, stats2, filename, title, label1='First Pass', label2='Second Pass'):
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

    plt.style.use('ggplot')
    categories = sorted(set(stats1) | set(stats2), key=lambda item: max(stats1.get(item, 0), stats2.get(item, 0)), reverse=True)
    values1 = [stats1.get(category, 0) for category in categories]
    values2 = [stats2.get(category, 0) for category in categories]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width / 2, values1, width, label=label1, color='#4ECDC4', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width / 2, values2, width, label=label2, color='#FF6B6B', edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Availability')
    ax.xaxis.labelpad = 12
    ax.set_ylabel('Count')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.tick_params(axis='x', pad=6)
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
