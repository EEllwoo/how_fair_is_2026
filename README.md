# Software artefacts for our FAIR evaluation literature review

Tools and scripts used in the process of gathering results for our paper "How FAIR is Research Software?"

## Authors

The contents of this repository were produced by Freddie Butterfield, Emma Ellwood, Jed Spooner and William Wood

## License

This project is licensed under the Apache License 2.0.

Copyright (c) 2026

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.

You may obtain a copy of the License at:
http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.


## Provenance

This software was worked on over several months in early 2026.

## File names and functions:


**Plotting Scripts:**

`FAIR_compliance.py` - This file finds how many of the reviewed papers are fully FAIR compliant, and prints a summary of the results.

`acm_badge_cascade.py` - This file plots the number of papers achieving each step of ACM badges as well as a violin plot of no. of FAIR criteria per ACM badge achievement.

`artifact_overlap.py` - This file plots the differences in found artefacts between the first and second pass.

`fair_criteria_distribution.py` - This file plots a graph showing the number of papers achieving a certain number of FAIR criteria, with shading representing what % of those papers had DOIs

`fair_criterion_compliance.py` - This file plots FAIR compliance for each letter, showing what % of papers achieved the criteria per letter.

`fair_letter_compliance.py` - This file plots how many papers achieved each *full* letter of FAIR.

`artefact_availability.py` - This file collects and plots how many of the reviewed papers we found had artefacts we could find. Prints results and plots some graphs, which can be found in the graphs folder.

`repository_stats.py` - This file collects and plots some information on which repositories are used.


**Processing Scripts:**

`compare_passes.py` - A script to compare two or more passes of our FAIR evaluation over a set of papers, and find disagreements between the different passes. To use: download compare_passes.py, put all evaluation results in the form of seperate CSV files into the 'results' folder, and run compare.py. The results of the comparison will be output to 'comparison.csv', with the disagreements in the form of [evaluation 1 answer] | [evaluation 2 answer] | ... | [evaluation n answer]

`find_missing_information.py` - This file compares a csv with a reference sheet of all the paper titles with their artefact DOIs to find any papers missing from the CSV.

`fix_missing_information.py` - This file finds and fixes any errors involving artefact DOIs in our results.

`pre_process.py` - This file converts a CSV file into a dataframe and does some basic pre-processing.

`scraper.py` - This file collects all the paper titles and their DOIs from the IEEE website.

`optimistic_dataset.py` - This file produces an "optimistic" dataset: if two reviewers have disagreed on a criterion between passes, take the result that says 'Yes'.


**Analysis Notebooks:**
These notebooks were made to make running our results as easy as a click of a button.

`data_reports.ipynb` - Fixes any issues with our results CSVs

`plot_gen.ipynb` - Plots our results data
