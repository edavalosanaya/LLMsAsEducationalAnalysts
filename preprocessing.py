import pathlib
import datetime
import json
from collections import defaultdict
import pathlib
import os
import random

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

assignment_names = ['Suffrage', 'Ants', 'Clouds', 'Waterclocks', 'Lizards', 'Tastes', 'Lodgepoles']
num_of_questions = [18, 5, 5, 5, 5, 5, 5]

# Merge GatesS ['Ants', 'Clouds', 'Waterclocks'] and GatesT [Lizards, 'Tastes', 'Lodgepoles']
final_assessments = ['Suffrage', 'GatesS', 'GatesT']
gates_list = {
    'GatesS': ['Ants', 'Clouds', 'Waterclocks'],
    'GatesT': ['Lizards', 'Tastes', 'Lodgepoles']
}

with open("./handpicked_top_features.json", "r") as f:
    top_features = json.load(f)['features']

dfs = pd.read_excel('./data/accumulative_metrics.xlsx', sheet_name=None)

# For all assignments, drop the following columns
for k, df in dfs.items():
    dfs[k] = df.drop(columns=['group', 'valor_MAP', f"{k}_score", f"{k}_session_count"])

    # Drop any rows that the field f"{k}_data_loss" is 1 or f"{k}_data_quality_is_good" is 0
    dfs[k] = dfs[k][dfs[k][f"{k}_data_loss"] == 0]
    dfs[k] = dfs[k][dfs[k][f"{k}_data_quality_is_good"] == 1] 

final_dfs = {}
for group in ['GatesS', 'GatesT']:
    within_group = gates_list[group]

    # Set 'id' as the index
    within_group_dfs = [dfs[assessment].set_index('id') for assessment in within_group]
    group_df = pd.concat(within_group_dfs, axis=1)

    # Reset the index
    group_df.reset_index(inplace=True)

    # Drop any rows that have NaN values
    # group_df.dropna(inplace=True)
    # Print the rows that have NaN values
    print(group_df[group_df.isnull().any(axis=1)])

    # Update score by computing total score
    columns_to_add = []
    for i, assessment in enumerate(within_group):
        assignment_num_of_questions = num_of_questions[assignment_names.index(assessment)]
        columns_to_add += [f"{assessment}_{i+1}" for i in range(assignment_num_of_questions)]

    group_df['total_score'] = group_df[columns_to_add].sum(axis=1)

    # Rename the item response columns from "Ants_1" to "GatesS_1"
    columns_to_rename = {}
    counter = 1
    for i, assessment in enumerate(within_group):
        assignment_num_of_questions = num_of_questions[assignment_names.index(assessment)]
        for j in range(assignment_num_of_questions):
            columns_to_rename[f"{assessment}_{j+1}"] = f"{group}_{counter}"
            counter += 1
    group_df.rename(columns=columns_to_rename, inplace=True)

    # Compute mean of the top features
    for f in top_features:
        group_df[f] = group_df[[f"{assessment}_{f}" for assessment in within_group]].mean(axis=1)

    # Columns to drop
    columns_to_drop = []
    for i, assessment in enumerate(within_group):
        columns_to_drop += [col for col in group_df.columns if col.startswith(assessment)]

    # Drop any columns where the assignment questions are NaN
    columns_to_check = [col for col in group_df.columns if col.startswith(group)]
    for col in columns_to_check:
        group_df = group_df.dropna(subset=[col])

    group_df = group_df.drop(columns=columns_to_drop)
    final_dfs[group] = group_df

# Add the Suffrage assessment
final_dfs['Suffrage'] = dfs['Suffrage']

# Save the final dataframes as a single excel file
with pd.ExcelWriter('./data/accumulative_metrics_aggregated.xlsx') as writer:
    for k, df in final_dfs.items():
        df.to_excel(writer, sheet_name=k, index=False)