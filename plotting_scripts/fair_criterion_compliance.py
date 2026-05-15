"""Plot individual letter compliance analysis by criterion."""

import matplotlib.pyplot as plt
import re
from plotting_scripts.FAIR_compliance import calculate_criterion_compliance_rates
from plotting_scripts.fair_letter_compliance import save_plot
from plotting_scripts.palette import FAIR_LETTER_COLORS, get_pgf_rc, FONTSIZE_AXES, FONTSIZE_LABELS


def plot_fair_criterion_compliance(df, F, A, I, R):
    """
    Generate subplots showing compliance rates for each criterion within each FAIR letter.
    
    Args:
        df: DataFrame with FAIR evaluation results
        F, A, I, R: Lists of criteria for each FAIR letter
    """
    # Create a figure with subplots for each FAIR letter
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    fair_letters = {'F': F, 'A': A, 'I': I, 'R': R}
    colors = FAIR_LETTER_COLORS

    for idx, (letter, criteria) in enumerate(fair_letters.items()):
        # Calculate compliance for each criterion using the new function
        criterion_compliance = calculate_criterion_compliance_rates(df, criteria)
        criterion_labels = []

        for criterion in criteria:
            if criterion in df.columns:
                # Shorten label for readability
                short_label = re.search(r"[FAIR](\d\.)+", criterion).group(0)
                criterion_labels.append(short_label)

        criterion_labels = criterion_labels[::-1]

        # Plot
        ax = axes[idx]
        bars = ax.barh(range(len(criterion_compliance)), criterion_compliance,
                       color=colors[idx], alpha=0.7, edgecolor='black')
        ax.set_yticks(range(len(criterion_labels)))
        ax.set_yticklabels(criterion_labels, fontsize=FONTSIZE_LABELS-4)
        ax.set_xlabel('Compliance Rate (%)', fontsize=FONTSIZE_AXES, fontweight='bold')
        ax.set_title(f'Letter {letter} - Compliance by Criterion', fontsize=FONTSIZE_AXES, fontweight='bold')
        ax.set_xlim(0, 100)

        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, criterion_compliance)):
            ax.text(value + 2, i, f'{value:.1f}%', va='center', fontsize=FONTSIZE_LABELS)

    #fig.suptitle('FAIR Criterion Compliance by Letter', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_plot(fig, title="fair_criterion_compliance")
    plt.show()


def main(df=None, F=None, A=None, I=None, R=None):
    """
    Generate individual FAIR criterion compliance plots.
    
    Args:
        df: DataFrame with FAIR evaluation results (optional).
        F, A, I, R: Lists of criteria for each FAIR letter (optional).
    """
    if df is not None and F is not None and A is not None and I is not None and R is not None:
        print("Generating FAIR criterion compliance plot...")
        plot_fair_criterion_compliance(df, F, A, I, R)


if __name__ == '__main__':
    main()
