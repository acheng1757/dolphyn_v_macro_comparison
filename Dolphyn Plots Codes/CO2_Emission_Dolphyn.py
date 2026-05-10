import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir


# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/Ethylene_Case/Results/Results_CSC/System_CO2_emission_balance.csv']
              #f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_CSC/System_CO2_emission_balance.csv',
              #f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_CSC/System_CO2_emission_balance.csv',
             # f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_CSC/System_CO2_emission_balance.csv']  # Replace with your actual file paths

scenario_names = ['Ethylene_Case'] #, 'HB-LS', 'LB-HS', 'LB-LS']

# Columns of interest for summation
columns_of_interest = ["Power Emissions", 
                       "HSC Emissions", 
                       "CSC Emissions", 
                       "Bio Elec Plant Emissions", 
                       "Biomass CO2 for Bio Elec", 
                       "Bio H2 Plant Emissions",
                       "Biomass CO2 for Bio H2", 
                       "Bio LF Plant Emissions", 
                       "Biomass CO2 for Bio LF", 
                       "Bio NG Plant Emissions", 
                       "Biomass CO2 for Bio NG", 
                       "Conventional NG", 
                       "Syn NG Plant Emissions", 
                       "Syn NG", 
                       "Bio NG", 
                       "Conventional Liquid Fuels", 
                       "Synfuel Plant Emissions", 
                       "Synfuels", 
                       "Biofuels", 
                       "NG Reduction from Power CCS", 
                       "NG Reduction from H2 CCS", 
                       "NG Reduction from DAC CCS"]


# Conversion factor (example)
conversion_factor = 1e-6  # Adjust as needed

# Initialize a dictionary to store values for each scenario
global_values_per_scenario = {}

# Process each file
for path, scenario in zip(file_paths, scenario_names):
    # Load the CSV file
    df = pd.read_csv(path, header=0)
    
    # Check if 'AnnualSum' exists in the first column (assumes the first column is for labels/identifiers)
    annual_sum_row = df[df.iloc[:, 0].str.contains('AnnualSum', na=False, case=False)]
    
    if not annual_sum_row.empty:
        # Extract values for the columns of interest
        extracted_values = annual_sum_row.iloc[0][columns_of_interest]  # Extract row as a Series
        # Convert values to float and apply conversion factor
        extracted_values = extracted_values.astype(float) * conversion_factor
    else:
        # Handle case where 'AnnualSum' row is not found
        extracted_values = pd.Series([0] * len(columns_of_interest), index=columns_of_interest)

    # Store the values for this scenario
    global_values_per_scenario[scenario] = extracted_values

# Convert the dictionary to a DataFrame for plotting
combined_data = pd.DataFrame(global_values_per_scenario).T  # Transpose for easier plotting

combine_mapping = {
    'Power Emissions': 'Conventional NG',
    "NG Reduction from Power CCS": 'Conventional NG',
    
    'HSC Emissions': 'Conventional NG',
    'NG Reduction from H2 CCS': 'Conventional NG',
    
    'CSC Emissions': 'DAC Capture',
    'NG Reduction from DAC CCS': 'DAC Capture',
    
    'Biomass CO2 for Bio Elec': 'Biomass Capture',
    'Biomass CO2 for Bio H2': 'Biomass Capture',
    'Biomass CO2 for Bio LF': 'Biomass Capture',
    'Biomass CO2 for Bio NG': 'Biomass Capture',
    
    'Bio Elec Plant Emissions': 'Biofuels process',
    'Bio H2 Plant Emissions': 'Biofuels process',
    'Bio LF Plant Emissions': 'Biofuels process',
    'Bio NG Plant Emissions': 'Biofuels process',
    'Biofuels': 'Biofuels process',
    'Bio NG': 'Biofuels processes',
    
    'Syn NG Plant Emissions': 'Synthetic NG and processes',
    'Syn NG': 'Synthetic NG and processes',
    
    'Synfuel Plant Emissions': 'Synthetic Fuels and processes',
    'Synfuels': 'Synthetic Fuels and processes',

}

# Apply the mapping to combine categories in the columns
combined_data = combined_data.rename(columns=combine_mapping)

# Group the combined data by the new category names and sum the values
combined_data = combined_data.groupby(by=combined_data.columns, axis=1).sum()

# Custom order for arranging categories
desired_order = [
    'Biomass Capture',
    'DAC Capture',
    'Conventional Liquid Fuels',
    'Conventional NG',
    'Synthetic Fuels and processes',
    'Synthetic NG and processes',
    'Biofuels',
    'Biofuels process',
    'Power Sector',
    'H2 Sector'
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

# Custom colors and display names
category_colors = {
    'Biomass Capture':'olivedrab',
    'DAC Capture':'darkblue',
    'Power Sector':'orange',
    'H2 Sector':'deepskyblue',
    'Conventional Liquid Fuels':'grey',
    'Conventional NG':'lightgrey',
    'Synthetic Fuels and processes':'purple',
    'Synthetic NG and processes':'violet',
    'Biofuels':'seagreen',
    'Biofuels process':'lightgreen'
}

category_names = {
    'Biomass Capture':'Biomass',
    'DAC Capture':'DAC',
    'Power Sector':'Power',
    'H2 Sector':'H2',
    'Conventional Liquid Fuels':'Fossil Liquid Fuels',
    'Conventional NG':'Fossil NG',
    'Synthetic Fuels and processes':'Synthetic Liquid Fuels',
    'Synthetic NG and processes':'Synthetic NG',
    'Biofuels process':'Bio Process Emissions',
    'Biofuels':'Bio Liquid Fuels'
}

plt.rcParams['font.family'] = 'Arial'

# Plotting the combined stacked horizontal bar chart with custom colors
fig, ax = plt.subplots(figsize=(4.3, 2.2))
combined_data.plot(kind='barh', stacked=True, width=0.7, ax=ax,
                   color=[category_colors.get(col, '#333333') for col in combined_data.columns])
plt.ylabel('Scenario', fontsize=16)
#plt.xlabel('CO2 Emission Balance (Mt)', fontsize=16)
plt.title('CO2 Emission Balance (Mt)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)

ax.set_xticks([-1500, -750, 0, 750, 1500])

# Set x-axis limits
ax.set_xlim(-1750, 1750)
ax.invert_yaxis()

# Add a vertical line at x=0
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')

# Remove legend
ax.legend().remove()

plt.tight_layout()
plt.show()