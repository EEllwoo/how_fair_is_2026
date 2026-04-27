"""
This file is designed to compare any number of CSVs containing the results 
of a pass of our artefact review over a set of papers.
"""

import pandas as pd
import os

def compare(results):
    # Read all CSV files into a list of review passes (dataframes)
    dataframes = [pd.read_csv(file) for file in results]
    
    # Set paper name as index
    for i in range(len(dataframes)):
        dataframes[i] = dataframes[i].set_index('Paper Name:')
    
    # Count all paper title occurences across all passes
    paper_counts = {}
    for df in dataframes:
        for paper in df.index:
            if paper not in paper_counts:
                paper_counts[paper] = 0
            paper_counts[paper] += 1


    # Get all matched papers (papers present in all passes)
    matched_papers = [paper for paper, count in paper_counts.items() if count == len(dataframes)]

    # Print all unmatched papers (papers not present in all passes)
    unmatched_papers = [paper for paper, count in paper_counts.items() if count < len(dataframes)]
    print("Unmatched Papers (present in only one pass):")
    for paper in unmatched_papers:
        print(f" - {paper}")

    # Get question columns
    questions = [col for col in dataframes[0].columns]

    # Construct rows for output CSV
    rows = []

    for paper in matched_papers:
        row = {"Paper Name:": paper}

        for q in questions:
            answers = []

            for df in dataframes:
                if paper in df.index:
                    answers.append(df.loc[paper, q])
                else:
                    answers.append("MISSING")

            # If all answers are the same, keep one
            if len(set(map(str, answers))) == 1:
                row[q] = answers[0]
            else:
                row[q] = " | ".join(map(str, answers))

        rows.append(row)

    # Construct output dataframe
    output_df = pd.DataFrame(rows)

    # Save comparison CSV
    output_df.to_csv("comparison.csv", index=False)


if __name__ == "__main__":
    dir = "results/"
    results = [
        os.path.join(dir, f)
        for f in os.listdir(dir)
        if f.endswith("_fixed.csv")
    ]
    compare(results)