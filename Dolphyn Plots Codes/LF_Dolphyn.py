import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Define paths and scenarios

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, scenario_names

print('dolphyn_base_dir: ', dolphyn_base_dir)

bf_results_files = [f'{dolphyn_base_dir}/B5_HB_HS_11w/Results/Results_BESC/BESC_Bio_LF_capacity.csv']

sf_results_files = [f'{dolphyn_base_dir}/B5_HB_HS_11w/Results/Results_LF/Synfuel_capacity.csv']


fuels_balance_files = {
    'Gasoline': [f'{dolphyn_base_dir}/B5_HB_HS_11w/Results/Results_LF/LF_Gasoline_balance.csv'],
    
    'Jetfuel': [f'{dolphyn_base_dir}/B5_HB_HS_11w/Results/Results_LF/LF_Jetfuel_balance.csv'],

    'Diesel': [f'{dolphyn_base_dir}/B5_HB_HS_11w/Results/Results_LF/LF_Diesel_balance.csv']
}

conversion_factor = 0.293071 * 3.6e-9

# Load results for scenarios
def load_bf_results(files, scenario_names):
    dfs = []
    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df['Scenario'] = scenario
        # Create a total biofuel production column
        df['Total_Biofuel_Production'] = (
            df['Annual_Biogasoline_Production'] +
            df['Annual_Biojetfuel_Production'] +
            df['Annual_Biodiesel_Production']
        ) * conversion_factor
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Categorize resources
def categorize_bf_resource(resource):
    if resource == 'Total':
        return None
    elif 'Gasoline_Gasification_CCS_99' in resource:
        return 'Bio MeOH - Gasoline High CCS'
    elif 'Gasoline_Gasification' in resource and 'CCS' not in resource:
        return 'Bio MeOH - Gasoline Non CCS'
    elif 'Pyrolysis_CCS_99' in resource:
        return 'Pyrolysis High CCS'
    elif 'Pyrolysis' in resource and 'CCS' not in resource:
        return 'Pyrolysis Non CCS'
    elif 'FT_High_Diesel_CCS_99' in resource:
        return 'Bio FT (High Diesel) High CCS'
    elif 'FT_High_Diesel' in resource and 'CCS' not in resource:
        return 'Bio FT (High Diesel) Non CCS'
    elif 'FT_High_Jetfuel_CCS_84' in resource:
        return 'Bio FT (High Jetfuel) CCS 84'
    elif 'FT_High_Jetfuel_CCS_99' in resource:
        return 'Bio FT (High Jetfuel) CCS 99'
    else:
        return None

def load_sf_results(files, scenario_names):
    dfs = []
    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df['Scenario'] = scenario
        # Create a total biofuel production column
        df['Total_Synfuel_Production'] = (
            df['Annual_Syngasoline_Production'] +
            df['Annual_Synjetfuel_Production'] +
            df['Annual_Syndiesel_Production']
        ) * conversion_factor
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# Categorize resources
def categorize_sf_resource(resource):
    if 'Synfuel_Plant' in resource and 'CCS' not in resource:
        return 'SFT Non CCS'
    elif 'Synfuel_Plant_wCCS' in resource:
        return 'SFT CCS'
    

# Load fossil fuel balance data — fix demand column
def load_fossil_fuel_balances(files, scenario_names):
    dfs = []
    for fuel_type, file_list in files.items():
        for file, scenario in zip(file_list, scenario_names):
            df = pd.read_csv(file)
            df['Scenario'] = scenario
            demand_value = pd.to_numeric(df.iloc[1, -2], errors='coerce') * conversion_factor
            fossil_value = pd.to_numeric(df.iloc[1, -3], errors='coerce') * conversion_factor
            
            df_result = pd.DataFrame({
                'Scenario': [scenario],
                'Fossil': [fossil_value],
                'Demand': [demand_value]
            })
            dfs.append(df_result)
    return pd.concat(dfs, ignore_index=True)

# Load biofuel results and categorize
bf_data = load_bf_results(bf_results_files, scenario_names)
bf_data['Resource_Category'] = bf_data['Resource'].apply(categorize_bf_resource)
bf_aggregated = bf_data.groupby(['Scenario', 'Resource_Category'])['Total_Biofuel_Production'].sum().unstack().fillna(0)

print(bf_data['Resource'].unique())
print(bf_data['Resource_Category'].unique())  # check for NaN

# Load synfuel results and categorize
sf_data = load_sf_results(sf_results_files, scenario_names)
sf_data['Resource_Category'] = sf_data['Resource'].apply(categorize_sf_resource)
sf_aggregated = sf_data.groupby(['Scenario', 'Resource_Category'])['Total_Synfuel_Production'].sum().unstack().fillna(0)


# Load fossil fuel results and categorize
fossil_data = load_fossil_fuel_balances(fuels_balance_files, scenario_names)
fossil_aggregated = fossil_data.groupby('Scenario')[['Fossil']].sum()
demand_aggregated = fossil_data.groupby('Scenario')[['Demand']].sum()  # total demand across fuels

# Combine all data
combined_data = bf_aggregated.join(fossil_aggregated, on='Scenario', how='left').fillna(0)
combined_data = sf_aggregated.join(combined_data, on='Scenario', how='left').fillna(0)

scenario_order = ['B5_HB_HS_11w']
combined_data = combined_data.loc[scenario_order]


# Custom order for arranging categories
desired_order = [
    'Bio MeOH - Gasoline Non CCS',
    'Bio MeOH - Gasoline High CCS',
    'Pyrolysis Non CCS',
    'Pyrolysis High CCS',
    'Bio FT (High Diesel) Non CCS',
    'Bio FT (High Diesel) High CCS',
    'Bio FT (High Jetfuel) CCS 84',
    'Bio FT (High Jetfuel) CCS 99',
    'SFT Non CCS',
    'SFT CCS',
    'Fossil'
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]


# Custom colors and display names
category_colors = {
    'Bio MeOH - Gasoline Non CCS':  'lightblue',
    'Bio MeOH - Gasoline High CCS': 'royalblue',
    'Pyrolysis Non CCS':            'peachpuff',
    'Pyrolysis High CCS':           'darkorange',
    'Bio FT (High Diesel) Non CCS': 'limegreen',
    'Bio FT (High Diesel) High CCS':'forestgreen',
    'Bio FT (High Jetfuel) CCS 84': 'sandybrown',
    'Bio FT (High Jetfuel) CCS 99': 'chocolate',
    'SFT Non CCS':                  'purple',
    'SFT CCS':                      'indigo',
    'Fossil':                       'grey',
}

plt.rcParams['font.family'] = 'Arial'

label_map = {
    'Bio MeOH - Gasoline Non CCS':  'Bio-MTG',
    'Bio MeOH - Gasoline High CCS': 'Bio-MTG CC99',
    'Pyrolysis Non CCS':            'Pyrolysis',
    'Pyrolysis High CCS':           'Pyrolysis CC99',
    'Bio FT (High Diesel) Non CCS': 'Bio-FT (Diesel)',
    'Bio FT (High Diesel) High CCS':'Bio-FT (Diesel) CC99',
    'Bio FT (High Jetfuel) CCS 84': 'Bio-FT (Jet) CC84',
    'Bio FT (High Jetfuel) CCS 99': 'Bio-FT (Jet) CC99',
    'SFT Non CCS':                  'Syn-FT',
    'SFT CCS':                      'Syn-FT CC99',
    'Fossil':                       'Fossil Liquids',
}

# Reorder the columns based on the desired order (only keep the matching columns)
available_order = [col for col in desired_order if col in combined_data.columns]
combined_data = combined_data[available_order]

# Plotting
fig, ax = plt.subplots(figsize=(4.3, 2.2))

combined_data[available_order].plot(
    kind='barh', stacked=True, width=0.7, ax=ax,
    color=[category_colors.get(col, '#333333') for col in available_order]
)

# Add demand as a vertical line per scenario
for i, scenario in enumerate(scenario_order):
    if scenario in demand_aggregated.index:
        demand_val = demand_aggregated.loc[scenario, 'Demand']
        ax.axvline(x=demand_val, color='black', linewidth=1.5, linestyle='--', label='Demand' if i == 0 else '')

plt.ylabel('Scenario', fontsize=16)
plt.title('Total LF Prod. (EJ)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)
ax.set_xlim(0, 13)
ax.set_xticks([0, 4, 8, 12])
ax.invert_yaxis()

# Legend — include demand line handle
handles, labels = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in available_order] + ['Demand']
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.15),
          ncol=5, fontsize=14, frameon=False)

plt.tight_layout()
plt.show()