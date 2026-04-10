import pandas as pd
import numpy as np
F = ["F1. Software is assigned a globally unique and persistent identifier (DOI)",
     "F1.1. Components of the software representing levels of granularity are assigned distinct identifiers. e.g. datasets. Software tools on their own are assumed to be sufficient granular so long as it is just the software.",
     "F1.2. Different versions of the software are assigned distinct identifiers.",
     "F2. Software is described with rich metadata. NOTE you can check the metadata from Zenodo by exporting to JSON at the bottom right of the page.",
     "F3. Metadata clearly and explicitly include the identifier of the software they describe. i.e. is the DOI in the metadata?",
     "F4. Metadata are FAIR, searchable and indexable. i.e. can I export it to a machine-readable format (usually yes if on Zenodo)"]
A = ["A1. Software is retrievable by its identifier using a standardised communications protocol. (Github DOES count)",
    "A1.1. The protocol is open, free, and universally implementable.",
    "A1.2. The protocol allows for an authentication and authorization procedure, where necessary.",
    "A2. Metadata are accessible, even when the software is no longer available."]
I = ["I1. Software reads, writes and exchanges data in a way that meets domain-relevant community standards. i.e. is it reading/writing to appropriate files e.g. JSON, CSV, or is data being taken from an API?",
     "I2. Software includes qualified references to other objects. e.g. This could mean datasets, etc not libraries",]
R = ["R1. Software is described with a plurality of accurate and relevant attributes. e.g. README, CITATION.cff, CONTRIBUTING.md",
     "R1.1. Software is given a clear and accessible license.",
     "R1.2. Software is associated with detailed provenance (version history).",
     "R2. Software includes qualified references to other software. e.g. external libraries, frameworks",
     "R3. Software meets domain-relevant community standards. i.e. well documented? docstrings? inline comments, indents okay?"]

# Mapping of FAIR letters to their criteria
FAIR_CRITERIA = {'F': F, 'A': A, 'I': I, 'R': R}


def Letter_compliance(df, title, letter):
    """Calculate the compliance of a given FAIR letter for a specific paper.

    A paper achieves a FAIR letter ONLY if it meets ALL criteria within that letter.
    Any 'No' answer means the letter is NOT achieved.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results.
        title (str): Paper name/title to check.
        letter (str): The FAIR letter to calculate compliance for (F, A, I, R).

    Returns:
        bool: True if paper achieves ALL criteria for this letter, False otherwise.
    """
    if letter not in FAIR_CRITERIA:
        raise ValueError("Invalid FAIR letter. Please choose from F, A, I, R.")

    criteria = FAIR_CRITERIA[letter]
    # Check ALL criteria for this letter - ALL must be met
    return all(is_criterion_compliant(df, title, criterion) for criterion in criteria)


# ===== HELPER FUNCTIONS =====

def get_value_safely(df, paper_name, criterion):
    """Safely extract a value from DataFrame, handling Series objects from duplicate indices.

    Args:
        df (pd.DataFrame): The dataframe to extract from
        paper_name (str): Name of the paper (index value)
        criterion (str): Column name to extract

    Returns:
        str: The value from the dataframe
    """
    value = df.loc[paper_name, criterion]
    if isinstance(value, pd.Series):
        return value.iloc[0]  # Take first value if duplicate indices
    return value


def is_criterion_compliant(df, paper_name, criterion):
    """Check if a single criterion is met by a paper.

    A criterion is considered compliant if the answer is "Yes", "Not Applicable", 
    or "Not necessary".

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results
        paper_name (str): Name of the paper to check
        criterion (str): Column name (criterion) to check

    Returns:
        bool: True if criterion is met, False otherwise (or if criterion doesn't exist)
    """
    if criterion not in df.columns:
        return False
    
    value = get_value_safely(df, paper_name, criterion)
    return value in ["Yes", "Not Applicable", "Not necessary", "Software is currently available"]


# ===== COMPLIANCE CALCULATION FUNCTIONS =====

def calculate_letter_compliance_rates(df, letter):
    """Calculate compliance rate for a specific FAIR letter across all papers.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results
        letter (str): The FAIR letter to calculate compliance for (F, A, I, R)

    Returns:
        float: Compliance rate as percentage (0-100)
    """
    compliant_count = 0
    total_papers = len(df)

    for paper_name in df.index:
        try:
            # Try using the existing Letter_compliance function
            if Letter_compliance(df, paper_name, letter):
                compliant_count += 1
        except:
            # Fallback: direct calculation if Letter_compliance fails
            compliant_count += _calculate_single_paper_compliance(df, paper_name, letter)

    return (compliant_count / total_papers) * 100


def _calculate_single_paper_compliance(df, paper_name, letter):
    """Helper function to calculate compliance for a single paper (fallback method).

    A paper achieves a FAIR letter ONLY if it meets ALL criteria within that letter.
    Any 'No' answer means the letter is NOT achieved.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results
        paper_name (str): Name of the paper to check
        letter (str): The FAIR letter to check (F, A, I, R)

    Returns:
        int: 1 if compliant, 0 if not compliant
    """
    if letter not in FAIR_CRITERIA:
        return 0
    
    criteria = FAIR_CRITERIA[letter]
    # Check ALL criteria for this letter - ALL must be met
    return 1 if all(is_criterion_compliant(df, paper_name, criterion) for criterion in criteria) else 0


def calculate_all_letter_compliance_rates(df):
    """Calculate compliance rates for all FAIR letters.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results

    Returns:
        dict: Dictionary with letters as keys and compliance rates as values
    """
    letters = ['F', 'A', 'I', 'R']
    return {letter: calculate_letter_compliance_rates(df, letter) for letter in letters}


def calculate_criterion_compliance_rates(df, criteria_list):
    """Calculate compliance rates for individual criteria within a FAIR letter.

    A criterion is considered compliant if the answer is "Yes", "Not Applicable", or "Not necessary".

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results
        criteria_list (list): List of criteria column names

    Returns:
        list: Compliance rates for each criterion as percentages
    """
    compliance_rates = []

    for criterion in criteria_list:
        if criterion in df.columns:
            compliant_count = sum(
                1 for paper_name in df.index 
                if is_criterion_compliant(df, paper_name, criterion)
            )
            compliance_rate = (compliant_count / len(df)) * 100
            compliance_rates.append(compliance_rate)
        else:
            compliance_rates.append(0.0)

    return compliance_rates


def calculate_all_criterion_compliance_rates(df):
    """Calculate compliance rates for ALL individual criteria across all FAIR letters.

    A criterion is considered compliant if the answer is "Yes", "Not Applicable", or "Not necessary".

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results

    Returns:
        dict: Dictionary with FAIR letters as keys, each containing a dict of criterion:compliance_rate pairs
    """
    results = {}

    # Define all criteria by letter
    all_criteria = {
        'F': F,
        'A': A,
        'I': I,
        'R': R
    }

    for letter, criteria_list in all_criteria.items():
        letter_results = {}

        for criterion in criteria_list:
            if criterion in df.columns:
                compliant_count = sum(
                    1 for paper_name in df.index 
                    if is_criterion_compliant(df, paper_name, criterion)
                )
                compliance_rate = (compliant_count / len(df)) * 100
                letter_results[criterion] = compliance_rate
            else:
                letter_results[criterion] = 0.0

        results[letter] = letter_results

    return results


def get_criterion_compliance_summary(df):
    """Generate a summary of individual criterion compliance rates.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results

    Returns:
        dict: Summary with overall statistics and detailed criterion breakdown
    """
    criterion_rates = calculate_all_criterion_compliance_rates(df)

    # Calculate summary statistics
    summary = {
        'criterion_rates': criterion_rates,
        'letter_summaries': {}
    }

    for letter, criteria_dict in criterion_rates.items():
        rates = list(criteria_dict.values())
        summary['letter_summaries'][letter] = {
            'average_compliance': sum(rates) / len(rates),
            'min_compliance': min(rates),
            'max_compliance': max(rates),
            'criteria_count': len(rates)
        }

    return summary


# ===== FULL FAIR COMPLIANCE ANALYSIS =====

def calculate_full_fair_compliance(df):
    """Calculate which papers meet ALL FAIR criteria (F, A, I, R).

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results

    Returns:
        tuple: (compliant_papers, non_compliant_papers) lists of paper names
    """
    compliant_papers = []
    non_compliant_papers = []

    for paper_name in df.index:
        # Check if paper meets all FAIR letters
        is_fully_compliant = True

        for letter in ['F', 'A', 'I', 'R']:
            try:
                if not Letter_compliance(df, paper_name, letter):
                    is_fully_compliant = False
                    break
            except:
                # Fallback check
                if _calculate_single_paper_compliance(df, paper_name, letter) == 0:
                    is_fully_compliant = False
                    break

        if is_fully_compliant:
            compliant_papers.append(paper_name)
        else:
            non_compliant_papers.append(paper_name)

    return compliant_papers, non_compliant_papers


# ===== SUMMARY FUNCTIONS =====

def get_fair_summary(df):
    """Generate a comprehensive FAIR compliance summary.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results

    Returns:
        dict: Summary statistics including compliance rates and paper counts
    """
    # Calculate compliance rates for each letter
    letter_rates = calculate_all_letter_compliance_rates(df)

    # Calculate full FAIR compliance
    compliant_papers, non_compliant_papers = calculate_full_fair_compliance(df)

    # Calculate overall statistics
    total_papers = len(df)
    full_compliance_rate = len(compliant_papers) / total_papers * 100

    return {
        'total_papers': total_papers,
        'letter_compliance_rates': letter_rates,
        'full_compliance_rate': full_compliance_rate,
        'compliant_papers': compliant_papers,
        'non_compliant_papers': non_compliant_papers,
        'compliant_count': len(compliant_papers),
        'non_compliant_count': len(non_compliant_papers)
    }


def print_fair_summary(df):
    """Print a formatted FAIR compliance summary.

    Args:
        df (pd.DataFrame): DataFrame containing the FAIR evaluation results
    """
    summary = get_fair_summary(df)

    print("=== FAIR COMPLIANCE SUMMARY ===")
    print(f"Total Papers Analyzed: {summary['total_papers']}")
    print()

    print("Compliance Rates by FAIR Letter:")
    for letter, rate in summary['letter_compliance_rates'].items():
        print(f"  {letter}: {rate:.1f}%")
    print()

    print(f"Full FAIR Compliance: {summary['full_compliance_rate']:.1f}%")
    print(f"  Compliant Papers: {summary['compliant_count']}")
    print(f"  Non-Compliant Papers: {summary['non_compliant_count']}")
    print()

    if summary['compliant_papers']:
        print("Fully Compliant Papers:")
        for paper in summary['compliant_papers']:
            print(f"  ✓ {paper}")
    else:
        print("No papers are fully FAIR compliant.")
            

