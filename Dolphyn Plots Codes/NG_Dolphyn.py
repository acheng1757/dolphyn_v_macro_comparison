#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May  1 01:18:06 2026

@author: junlaw
"""
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir

# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_NG/NG_Balance.csv',
              f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_NG/NG_Balance.csv',
              f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_NG/NG_Balance.csv',
              f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_NG/NG_Balance.csv']  # Replace with your actual file paths

scenario_names = ['HB-HS', 'HB-LS', 'LB-HS', 'LB-LS']

# Columns of interest for summation
columns_of_interest = ["Syn_NG", "Conventional_NG", "NG_Demand", "Power", "H2", "CSC", "BESC"]

# Custom colors for each category
category_colors = {
    "Syn_NG": "violet",
    "Conventional_NG": "lightgrey",
    "NG_Demand": "bisque",
    "Power": "orange",
    "H2": "deepskyblue",
    "CSC": "darkblue"
}

# Custom display names for each category
category_names = {
    "Syn_NG": "Syn. NG",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC "
}

# Specify desired order for the columns
desired_order = ["NG_Demand", 
                 "Power",
                 "CSC",
                 "Syn_NG", 
                 "Conventional_NG"]

# Conversion factor (example: converting values to a different unit)
conversion_factor = 0.293071*3.6e-9  # Adjust the conversion factor as needed

# Initialize a dictionary to store global values for each scenario
global_values_per_scenario = {}

# Process each file
for path, scenario in zip(file_paths, scenario_names):
    # Load the CSV file
    df = pd.read_csv(path, header=0)
    
    # Extract the 'AnnualSum' row by searching for it (assuming it's in the second row, index 1)
    annual_sum_row = df[df.iloc[:, 0] == 'AnnualSum']
    
    if not annual_sum_row.empty:
        # Select columns of interest and sum across zones
        global_values = {}
        for col in columns_of_interest:
            # Sum across zones for this column and apply unit conversion
            col_values = annual_sum_row.filter(like=col, axis=1).astype(float).sum(axis=1).values * conversion_factor
            global_values[col] = col_values[0] if col_values.size > 0 else 0
    else:
        # Handle case where 'AnnualSum' row is not found
        global_values = {col: 0 for col in columns_of_interest}
    
    # Store the global values for this scenario
    global_values_per_scenario[scenario] = global_values

# Convert the global values dictionary to a DataFrame for plotting
combined_data = pd.DataFrame(global_values_per_scenario).T  # Transpose for easier plotting

# Reorder columns based on the desired order
combined_data = combined_data[desired_order]

# Rename the columns using the custom display names
combined_data = combined_data.rename(columns=category_names)

# Ensure colors match the desired order
ordered_colors = [category_colors[col] for col in desired_order]

# Plotting with your desired format
plt.rcParams['font.family'] = 'Arial'

# Plotting the combined stacked horizontal bar chart
fig, ax = plt.subplots(figsize=(3.6, 2.9))
combined_data.plot(
    kind='barh', stacked=True, width=0.7, ax=ax,
    color=[category_colors[col] for col in desired_order]
)

plt.ylabel('Scenario', fontsize=16)
plt.title('NG Balance (EJ)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)
ax.set_xlim(-12, 12)
ax.set_xticks([-10, -5, 0, 5, 10])
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

# Add custom legend with renamed labels
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in desired_order]
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
          ncol=2, fontsize=14, frameon=False)
#ax.legend().remove()
plt.tight_layout()
plt.show()
