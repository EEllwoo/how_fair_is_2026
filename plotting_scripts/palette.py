"""Shared IBM plotting palette helpers."""

from matplotlib.colors import LinearSegmentedColormap


IBM_YELLOW = "#ffb000"
IBM_ORANGE = "#fe6100"
IBM_MAGENTA = "#dc267f"
IBM_PURPLE = "#785ef0"
IBM_BLUE = "#648fff"

IBM_PALETTE = [IBM_YELLOW, IBM_ORANGE, IBM_MAGENTA, IBM_PURPLE, IBM_BLUE]

# Match the closest prior roles in the existing plots.
PASS_COLORS = [IBM_BLUE, IBM_MAGENTA, IBM_YELLOW]
FAIR_LETTER_COLORS = [IBM_MAGENTA, IBM_BLUE, IBM_PURPLE, IBM_ORANGE]
BADGE_CASCADE_COLORS = [IBM_YELLOW, IBM_ORANGE, IBM_MAGENTA, IBM_BLUE]
FULL_FAIR_CATEGORY_COLORS = [IBM_BLUE, IBM_MAGENTA, IBM_ORANGE, IBM_PURPLE]

PGF_FONT_RC = {
    "font.size": 12,
    "font.weight": "bold",
    "axes.titlesize": 10,
    "figure.titlesize": 10,
    "legend.fontsize": 10,
    "legend.title_fontsize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
}

FONTSIZE_AXES = 18
FONTSIZE_LABELS = 16
FONTSIZE_LEGEND = 12
FONTSIZE_TEXT = 14


def ibm_colormap(name, colors=None):
    """Build a matplotlib colormap from the IBM palette."""
    return LinearSegmentedColormap.from_list(name, colors or IBM_PALETTE)


def get_pgf_rc(tex_engine):
    """Return consistent PGF export settings for IBM-styled plots."""
    return {
        "pgf.texsystem": tex_engine,
        "text.usetex": True,
        "pgf.preamble": r"\usepackage[utf8x]{inputenc}" + "\n" + r"\usepackage[T1]{fontenc}",
        **PGF_FONT_RC,
    }
