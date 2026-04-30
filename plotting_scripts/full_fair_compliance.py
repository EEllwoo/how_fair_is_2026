"""Plot full FAIR compliance distribution."""

import matplotlib.pyplot as plt
from plotting_scripts.FAIR_compliance import calculate_full_fair_compliance
from plotting_scripts.fair_letter_compliance import save_plot


def plot_full_fair_compliance(df):
    """
    Generate pie chart showing what proportion of papers are fully FAIR compliant vs not.
    
    Args:
        df: DataFrame with FAIR evaluation results
    """
    compliant_papers, non_compliant_papers = calculate_full_fair_compliance(df)

    # Create pie chart showing full FAIR compliance
    labels = ['Fully FAIR Compliant', 'Not Fully Compliant']
    sizes = [len(compliant_papers), len(non_compliant_papers)]
    colors = ['#4CAF50', '#FF6B6B']  # Green for compliant, red for non-compliant
    explode = (0.1, 0)  # explode the compliant slice

    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', startangle=90, shadow=True)

    # Style the text
    for text in texts:
        text.set_fontsize(12)
        text.set_fontweight('bold')
    for autotext in autotexts:
        autotext.set_fontsize(12)
        autotext.set_fontweight('bold')

    ax.set_title('Full FAIR Compliance Distribution', fontsize=14, fontweight='bold')

    # Add legend with counts
    ax.legend(wedges, [f'{label}: {count} papers' for label, count in zip(labels, sizes)],
              title='Compliance Status', loc='center left', bbox_to_anchor=(1, 0, 0.5, 1))

    plt.tight_layout()
    save_plot(fig)
    plt.style.use('ggplot')
    plt.show()
