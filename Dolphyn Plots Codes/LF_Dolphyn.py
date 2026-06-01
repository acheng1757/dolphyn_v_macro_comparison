import pandas as pd
import matplotlib.pyplot as plt
import os
import sys

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# Define paths and scenarios

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

print('dolphyn_base_dir: ', dolphyn_base_dir)

bf_results_files = [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_BESC/BESC_Bio_LF_capacity.csv']

sf_results_files = [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_LF/Synfuel_capacity.csv']


fuels_balance_files = {
    'Gasoline': [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_LF/LF_Gasoline_balance.csv'],

    'Jetfuel': [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_LF/LF_Jetfuel_balance.csv'],

    'Diesel': [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_LF/LF_Diesel_balance.csv']
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
    

FOSSIL_COL = {
    'Gasoline': 'Conventional_Gasoline',
    'Jetfuel':  'Conventional_Jetfuel',
    'Diesel':   'Conventional_Diesel',
}
DEMAND_COL = {
    'Gasoline': 'Gasoline_Demand',
    'Jetfuel':  'Jetfuel_Demand',
    'Diesel':   'Diesel_Demand',
}
BIO_COL = {
    'Gasoline': 'Bio_Gasoline',
    'Jetfuel':  'Bio_Jetfuel',
    'Diesel':   'Bio_Diesel',
}
SYN_COL = {
    'Gasoline': 'Syn_Gasoline',
    'Jetfuel':  'Syn_Jetfuel',
    'Diesel':   'Syn_Diesel',
}


def read_global_annualsum(file, target_col):
    """Return the AnnualSum value for the Global zone of target_col.
    Reads without header so the Zone row identifies which repeated
    column occurrence is the Global one."""
    df_raw = pd.read_csv(file, header=None)
    col_names = df_raw.iloc[0]
    zone_ids  = df_raw.iloc[1]
    mask = df_raw.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)
    if not mask.any():
        return 0.0
    annual_row = df_raw[mask].iloc[0]
    for i in range(1, len(col_names)):
        if (str(col_names.iloc[i]).strip() == target_col and
                str(zone_ids.iloc[i]).strip() == 'Global'):
            return pd.to_numeric(annual_row.iloc[i], errors='coerce') * conversion_factor
    return 0.0


def load_fossil_fuel_balances(files, scenario_names):
    dfs = []
    for fuel_type, file_list in files.items():
        fossil_col = FOSSIL_COL[fuel_type]
        demand_col = DEMAND_COL[fuel_type]
        for file, scenario in zip(file_list, scenario_names):
            df = pd.read_csv(file)
            annual_row = df[df.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)]
            fossil_value = pd.to_numeric(annual_row[fossil_col].values[0], errors='coerce') * conversion_factor
            demand_value = pd.to_numeric(annual_row[demand_col].values[0], errors='coerce') * conversion_factor
            dfs.append(pd.DataFrame({
                'Scenario': [scenario],
                'Fossil':   [fossil_value],
                'Demand':   [demand_value],
            }))
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

# Read Bio and Syn totals directly from balance file Global columns for cross-referencing
bio_balance_totals = {s: 0.0 for s in scenario_names}
syn_balance_totals = {s: 0.0 for s in scenario_names}
for fuel_type, file_list in fuels_balance_files.items():
    for file, scenario in zip(file_list, scenario_names):
        bio_balance_totals[scenario] += read_global_annualsum(file, BIO_COL[fuel_type])
        syn_balance_totals[scenario] += read_global_annualsum(file, SYN_COL[fuel_type])

# Compute AnnualSum row totals per fuel type for balance check
annualsum_row_totals = {}  # {scenario: {fuel_type: row_total}}
for fuel_type, file_list in fuels_balance_files.items():
    for file, scenario in zip(file_list, scenario_names):
        df = pd.read_csv(file)
        annual_row = df[df.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)]
        if not annual_row.empty:
            numeric_vals = annual_row.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
            total = numeric_vals.sum(axis=1).values[0] * conversion_factor
        else:
            total = 0.0
        annualsum_row_totals.setdefault(scenario, {})[fuel_type] = total

# Combine all data
combined_data = bf_aggregated.join(fossil_aggregated, on='Scenario', how='left').fillna(0)
combined_data = sf_aggregated.join(combined_data, on='Scenario', how='left').fillna(0)
combined_data = combined_data.join(demand_aggregated, on='Scenario', how='left').fillna(0)

scenario_order = scenario_names
combined_data = combined_data.loc[scenario_order]

# Cross-reference: add residual production not captured by capacity-file categories
for scenario in scenario_order:
    bio_from_capacity = bf_aggregated.loc[scenario].sum() if scenario in bf_aggregated.index else 0.0
    missing_bio = bio_balance_totals.get(scenario, 0.0) - bio_from_capacity
    if abs(missing_bio) > 1e-6:
        combined_data.loc[scenario, 'Other Bio LF'] = missing_bio

    syn_from_capacity = sf_aggregated.loc[scenario].sum() if scenario in sf_aggregated.index else 0.0
    missing_syn = syn_balance_totals.get(scenario, 0.0) - syn_from_capacity
    if abs(missing_syn) > 1e-6:
        combined_data.loc[scenario, 'Other Syn LF'] = missing_syn

combined_data = combined_data.fillna(0)


# Custom order for arranging categories
desired_order = [
    'Demand',
    'Bio MeOH - Gasoline Non CCS',
    'Bio MeOH - Gasoline High CCS',
    'Pyrolysis Non CCS',
    'Pyrolysis High CCS',
    'Bio FT (High Diesel) Non CCS',
    'Bio FT (High Diesel) High CCS',
    'Bio FT (High Jetfuel) CCS 84',
    'Bio FT (High Jetfuel) CCS 99',
    'Other Bio LF',
    'SFT Non CCS',
    'SFT CCS',
    'Other Syn LF',
    'Fossil'
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]


# Custom colors and display names
category_colors = {
    'Demand':                        'bisque',
    'Bio MeOH - Gasoline Non CCS':  'lightblue',
    'Bio MeOH - Gasoline High CCS': 'royalblue',
    'Pyrolysis Non CCS':            'peachpuff',
    'Pyrolysis High CCS':           'darkorange',
    'Bio FT (High Diesel) Non CCS': 'limegreen',
    'Bio FT (High Diesel) High CCS':'forestgreen',
    'Bio FT (High Jetfuel) CCS 84': 'sandybrown',
    'Bio FT (High Jetfuel) CCS 99': 'chocolate',
    'Other Bio LF':                 'darkseagreen',
    'SFT Non CCS':                  'purple',
    'SFT CCS':                      'indigo',
    'Other Syn LF':                 'mediumpurple',
    'Fossil':                       'grey',
}

plt.rcParams['font.family'] = 'Arial'

label_map = {
    'Demand':                        'Demand',
    'Bio MeOH - Gasoline Non CCS':  'Bio-MTG',
    'Bio MeOH - Gasoline High CCS': 'Bio-MTG CC99',
    'Pyrolysis Non CCS':            'Pyrolysis',
    'Pyrolysis High CCS':           'Pyrolysis CC99',
    'Bio FT (High Diesel) Non CCS': 'Bio-FT (Diesel)',
    'Bio FT (High Diesel) High CCS':'Bio-FT (Diesel) CC99',
    'Bio FT (High Jetfuel) CCS 84': 'Bio-FT (Jet) CC84',
    'Bio FT (High Jetfuel) CCS 99': 'Bio-FT (Jet) CC99',
    'Other Bio LF':                 'Other Bio LF',
    'SFT Non CCS':                  'Syn-FT',
    'SFT CCS':                      'Syn-FT CC99',
    'Other Syn LF':                 'Other Syn LF',
    'Fossil':                       'Fossil Liquids',
}

# Reorder the columns based on the desired order (only keep the matching columns)
available_order = [col for col in desired_order if col in combined_data.columns]
combined_data = combined_data[available_order]

# Plotting
fig, ax = plt.subplots(figsize=(9, 3.5))

combined_data[available_order].plot(
    kind='barh', stacked=True, width=0.7, ax=ax,
    color=[category_colors.get(col, '#333333') for col in available_order]
)

ax.axvline(x=0, color='black', linewidth=1, linestyle='--')

plt.ylabel('Scenario', fontsize=10)
plt.title('Total LF Balance (EJ)', fontsize=11)
plt.yticks(fontsize=9)
plt.xticks(fontsize=9)
ax.set_xlim(-14, 14)
ax.set_xticks([-12, -8, -4, 0, 4, 8, 12])
ax.invert_yaxis()

handles, labels = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in available_order]
legend = ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.12),
                   ncol=7, fontsize=8, frameon=True, framealpha=0.9)

plt.tight_layout()
fig.subplots_adjust(bottom=0.25)
plt.show()

# Print flow summary for each scenario
print()
for scenario in combined_data.index:
    row = combined_data.loc[scenario]
    pos_sum = row[row > 0].sum()
    neg_sum = row[row < 0].sum()
    net_sum = row.sum()
    totals = annualsum_row_totals.get(scenario, {})
    combined_total = sum(totals.values())
    print(f'Scenario: {scenario}')
    for fuel_type in ('Gasoline', 'Jetfuel', 'Diesel'):
        print(f'  AnnualSum row total ({fuel_type:8s}) : {totals.get(fuel_type, float("nan")):+.4f} EJ')
    print(f'  AnnualSum row total (combined) : {combined_total:+.4f} EJ')
    print(f'  Plot net                       : {net_sum:+.4f} EJ  (pos: {pos_sum:+.4f} EJ,  neg: {neg_sum:+.4f} EJ)')
    print()