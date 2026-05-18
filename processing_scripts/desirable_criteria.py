"""
This file prints out information relating to the desirable criteria we set. It does not plot anything as we believe
graphs for these stats are less important.
"""
import pandas as pd

def get_desirable_criteria_stats_yes_no(df, criterion):
    """
    Gets a basic statistic for desirable criteria that can be answered with yes/no

    Args:
        df: The DataFrame with the paper data
        criterion: The criterion or column label
    """
    count = 0
    for _, row in df.iterrows():
        criteria_met = row[criterion] == 'Yes'
        if criteria_met:
            count += 1

    print(f"{count} out of {len(df)} papers have achieved criterion: {criterion}. ({(count / len(df)):.2f}%)")

def get_desirable_criteria_stats_checkbox(df, criterion):
    """
    Gets a distribution of statistics for desirable criteria that used a checkbox

    Args:
        df: The DataFrame with the paper data
        criterion: The criterion or column label
    """
    counts = {"total": 0}
    for _, row in df.iterrows():
        results = row[criterion]
        if pd.isnull(results):
            continue

        counts['total'] += 1
        results = results.split(',')
        for r in results:
            r = r.strip()
            if r not in counts:
                counts[r] = 1
            else:
                counts[r] += 1

    print(f"Distribution for {criterion}")
    for key, value in counts.items():
        print(f"Key: {key}. Count: {value} out of {len(df)} papers ({(value / len(df)):.2f}%). ")

def desirable_criteria_main(df):
    criteria_yes_no = [
        'Has the software artefact been mentioned or cited in the paper for ease of findability?',
        'Does the software require the use of any 3rd party tools in order to execute it?'
    ]

    criteria_checkbox = [
        'Have any containerisation engines / orchestrators been employed in the reuse of the software?',
        'Is the software itself documented well? Which of the following code readability standards have been implemented?',
        'R2 follow-up: Is there a file / project manager tool to help with the installation of other software / libraries?'
    ]

    for c in criteria_yes_no:
        get_desirable_criteria_stats_yes_no(df, c)
    
    for c in criteria_checkbox:
        get_desirable_criteria_stats_checkbox(df, c)

