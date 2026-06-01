import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_NG/NG_Balance.csv']

# Columns of interest for summation
columns_of_interest = ["Syn_NG", "Bio_NG", "Conventional_NG", "NG_Demand", "Power", "H2", "CSC", "BESC", "Ethylene Consumption", "Ethylene Production"]

# Custom colors for each category
category_colors = {
    "Syn_NG": "violet",
    "Bio_NG": "seagreen",
    "Conventional_NG": "lightgrey",
    "NG_Demand": "bisque",
    "Power": "orange",
    "H2": "deepskyblue",
    "CSC": "darkblue",
    "BESC": "mediumseagreen",
    "Ethylene": "red",
}

# Custom display names for each category
category_names = {
    "Syn_NG": "Syn. NG",
    "Bio_NG": "Bio NG Prod.",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC",
    "BESC": "Bio NG Prod.",
    "Ethylene Consumption": "Ethylene",
    "Ethylene Production": "Ethylene",
}

# Specify desired order for the columns
desired_order = [
    "NG_Demand",
    "Power",
    "H2",
    "CSC",
    "BESC",
    "Ethylene",
    "Syn_NG",
    "Bio_NG",
    "Conventional_NG",
]

# Conversion factor (example: converting values to a different unit)
conversion_factor = 0.293071*3.6e-9  # Adjust the conversion factor as needed

# Initialize a dictionary to store global values for each scenario
global_values_per_scenario = {}
annualsum_row_totals = {}

# Process each file
for path, scenario in zip(file_paths, scenario_names):
    # Load the CSV file
    df = pd.read_csv(path, header=0)

    # Extract the 'AnnualSum' row by searching for it (assuming it's in the second row, index 1)
    annual_sum_row = df[df.iloc[:, 0] == 'AnnualSum']

    if not annual_sum_row.empty:
        # Full AnnualSum row total: sum all numeric columns across all zones
        numeric_vals = annual_sum_row.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        annualsum_row_totals[scenario] = numeric_vals.sum(axis=1).values[0] * conversion_factor

        # Select columns of interest and sum across zones
        global_values = {}
        for col in columns_of_interest:
            # Sum across zones for this column and apply unit conversion
            col_values = annual_sum_row.filter(like=col, axis=1).astype(float).sum(axis=1).values * conversion_factor
            global_values[col] = col_values[0] if col_values.size > 0 else 0
    else:
        # Handle case where 'AnnualSum' row is not found
        global_values = {col: 0 for col in columns_of_interest}
        annualsum_row_totals[scenario] = 0.0

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
plt.yticks(fontsize=14)
plt.xticks(fontsize=14)
ax.set_xlim(-12, 12)
ax.set_xticks([-10, -5, 0, 5, 10])
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

# Add custom legend with renamed labels
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in desired_order]
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.35),
          ncol=3, fontsize=12, frameon=False)

plt.subplots_adjust(left=0.30, right=0.98, top=0.88, bottom=0.50)
plt.show()

# Print flow summary for each scenario
print()
for scenario in combined_data.index:
    row = combined_data.loc[scenario]
    pos_sum = row[row > 0].sum()
    neg_sum = row[row < 0].sum()
    net_sum = row.sum()
    row_total = annualsum_row_totals.get(scenario, float('nan'))
    print(f'Scenario: {scenario}')
    print(f'  AnnualSum row total : {row_total:+.4f} EJ')
    print(f'  Plot net            : {net_sum:+.4f} EJ  (pos: {pos_sum:+.4f} EJ,  neg: {neg_sum:+.4f} EJ)')
    print()
