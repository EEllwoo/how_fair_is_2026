"""Plot ACM badge compliance cascade."""

import matplotlib.pyplot as plt
from processing_scripts.pre_process import scleaned_pandas
from plotting_scripts.fair_letter_compliance import save_plot


def plot_acm_badge_cascade(sample_file):
    """
    Generate bar chart showing ACM badge compliance cascade (no badge -> available -> functional -> reusable).
    
    Args:
        sample_file: Path to the CSV file with FAIR evaluation results
    """
    acm_badge_column = "Which (if any) ACM Badges does the report have?"

    # Use the wider pass data (no FAIR-essential filtering or dropped columns)
    wide_df = scleaned_pandas(sample_file, index_col="Paper Name:")

    if acm_badge_column not in wide_df.columns:
        raise ValueError(f"Missing ACM badge column: {acm_badge_column}")

    badge_text = wide_df[acm_badge_column].fillna("").astype(str).str.lower()

    has_available = badge_text.str.contains("artefact available")
    has_functional = badge_text.str.contains("artefact functional")
    has_reusable = badge_text.str.contains("artefact reusable")

    # Exclusive cascade buckets
    no_badge_count = (~has_available & ~has_functional & ~has_reusable).sum()
    available_only_count = (has_available & ~has_functional & ~has_reusable).sum()
    functional_only_count = (has_available & has_functional & ~has_reusable).sum()
    reusable_count = (has_available & has_functional & has_reusable).sum()

    cascade_labels = [
        "No badge",
        "Available only",
        "Functional only",
        "Reusable",
    ]
    cascade_counts = [
        int(no_badge_count),
        int(available_only_count),
        int(functional_only_count),
        int(reusable_count),
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        cascade_labels,
        cascade_counts,
        color=["#B0BEC5", "#90CAF9", "#42A5F5", "#1E88E5"],
        edgecolor="black",
        alpha=0.9,
    )

    ax.set_xlabel("Highest ACM Badge Awarded", fontsize=12)
    ax.set_ylabel("Number of papers", fontsize=12)
    ax.set_title("ACM Badge Compliance Cascade", fontsize=14, fontweight="bold")

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    save_plot(fig)
    plt.show()
