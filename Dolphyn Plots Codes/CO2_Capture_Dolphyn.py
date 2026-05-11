import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/Ethylene_Case/{dolphyn_results_folder}/Results_CSC/Zone_CO2_storage_balance.csv']
              #f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_CSC/Zone_CO2_storage_balance.csv',
              #f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_CSC/Zone_CO2_storage_balance.csv',
              #f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_CSC/Zone_CO2_storage_balance.csv']  # Replace with your actual file paths

# Columns of interest for summation
columns_of_interest = ["DAC Capture",
                       "Bio Elec Capture", 
                       "Bio H2 Capture", 
                       "Bio LF Capture", 
                       "Bio NG Capture", 
                       "Synfuel Plant Capture",
                       "Synfuel Plant Consumption",
                       "Syn NG Plant Capture",
                       "Syn NG Plant Consumption",
                       "NG Power CCS",
                       "NG DAC CCS",
                       "CO2 Storage",
                       "Ethylene Production",
                       "Bio Ethanol Capture"]


# Conversion factor (example: converting values to a different unit)
conversion_factor = 1e-6  # Adjust the conversion factor as needed

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

combine_mapping = {
    'NG DAC CCS': 'DAC Capture',
    
    'Bio Elec Capture': 'Biomass Capture',
    'Bio H2 Capture': 'Biomass Capture',
    'Bio LF Capture': 'Biomass Capture',
    'Bio NG Capture': 'Biomass Capture',

    'Syn NG Plant Capture': 'Synthetic NG',
    'Syn NG Plant Consumption': 'Synthetic NG',
    
    'Synfuel Plant Capture': 'Synthetic Fuels',
    'Synfuel Plant Consumption': 'Synthetic Fuels',

    'Ethylene Production': 'Ethylene Capture',
    'Bio Ethanol Capture': 'Bio Ethanol Capture',
}

# Apply the mapping to combine categories in the columns
combined_data = combined_data.rename(columns=combine_mapping)

# Group the combined data by the new category names and sum the values
combined_data = combined_data.groupby(by=combined_data.columns, axis=1).sum()

# Custom order for arranging categories
desired_order = [
    'CO2 Storage',
    'Synthetic Fuels',
    'Synthetic NG',
    'NG Power CCS',
    'NG H2 CCS',
    'DAC Capture',
    'Biomass Capture',
    'Ethylene Capture',
    'Bio Ethanol Capture'
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

# Custom colors and display names
category_colors = {
    'Biomass Capture':'olivedrab',
    'DAC Capture':'darkblue',
    'NG Power CCS':'orange',
    'NG H2 CCS':'deepskyblue',
    'Synthetic Fuels':'purple',
    'Synthetic NG':'violet',
    'CO2 Storage':'darkgoldenrod',
    'Ethylene Capture':'#9b59b6',
    'Bio Ethanol Capture':'#f5c518'
    }

category_names = {
    'CO2 Storage':'CO2 Storage',
    'Synthetic NG':'Syn. NG',
    'Synthetic Fuels':'Syn. Liquids',
    'NG Power CCS':'Power CCS',
    'NG H2 CCS':'H2 CCS',
    'DAC Capture':'DAC',
    'Biomass Capture':'Biofuel CCS',
    'Ethylene Capture':'Ethylene CCS',
    'Bio Ethanol Capture':'Bio Ethanol CCS',
}

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'

# Ensure the column order follows the legend order
desired_order = [col for col in category_names if col in combined_data.columns]
combined_data = combined_data[desired_order]

# Plotting
fig, ax = plt.subplots(figsize=(4.3, 2.8))
combined_data.plot(kind='barh', stacked=True, width=0.7, ax=ax,
                   color=[category_colors.get(col, '#333333') for col in combined_data.columns])

# Axis labels and title
plt.ylabel('Scenario', fontsize=16)
plt.title('Captured CO2 Balance (Mt)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)
#ax.set_xlim(-1250, 1250)
ax.set_xlim(-100, 100) # smaller set for ethylene only case
ax.set_xticks([-100, 0, 100])

ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

# Add small bar indicators for target values
indicator_height = 0.2
#target_values = {'HB-HS': -865.8, 'HB-LS': -433.8, 'LB-HS': -865.8, 'LB-LS': -433.8}
#for i, scenario in enumerate(combined_data.index):
#    target_value = target_values.get(scenario, None)
#    if target_value is not None:
#        ax.barh(i, 20, height=indicator_height, color='black', alpha=0.8, left=target_value)

# Custom legend
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in combined_data.columns]
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
          ncol=2, fontsize=14, frameon=False)
          
#ax.legend().remove()
plt.tight_layout()
plt.show()