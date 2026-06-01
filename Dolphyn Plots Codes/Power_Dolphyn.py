import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import sys

pd.set_option('display.max_columns', None)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

##########################################################################################################################################################

Power_Demand_EJ = 20.79194776
conversion_factor = 3.6e-9

scen = scenario_names[0]
scen_dir = os.path.join(dolphyn_base_dir, scen)

##########################################################################################################################################################

# Load Results files
df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'capacity_multi_sector.csv'))
df['Scenario'] = scen

sf_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_LF', 'Synfuel_capacity.csv'))
sf_df['Scenario'] = scen
sf_process_df = pd.read_csv(os.path.join(scen_dir, 'LFSC_Synfuel_Resources.csv'))

syn_ng_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_NG', 'Syn_ng_capacity.csv'))
syn_ng_df['Scenario'] = scen
syn_ng_process_df = pd.read_csv(os.path.join(scen_dir, 'NGSC_Syn_NG_Resources.csv'))

hsc_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_HSC', 'HSC_generation_storage_capacity.csv'))
hsc_df['Scenario'] = scen
hsc_process_df = pd.read_csv(os.path.join(scen_dir, 'HSC_generation.csv'))

bio_LF_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_BESC', 'BESC_Bio_LF_capacity.csv'))
bio_LF_df['Scenario'] = scen
bio_LF_process_df = pd.read_csv(os.path.join(scen_dir, 'BESC_Bio_Liquid_Fuels.csv'))

bio_H2_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_BESC', 'BESC_Bio_H2_capacity.csv'))
bio_H2_df['Scenario'] = scen
bio_H2_process_df = pd.read_csv(os.path.join(scen_dir, 'BESC_Bio_H2.csv'))

bio_Electricity_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_BESC', 'BESC_Bio_Electricity_capacity.csv'))
bio_Electricity_df['Scenario'] = scen
bio_Electricity_process_df = pd.read_csv(os.path.join(scen_dir, 'BESC_Bio_Electricity.csv'))

bio_NG_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_BESC', 'BESC_Bio_NG_capacity.csv'))
bio_NG_df['Scenario'] = scen
bio_NG_process_df = pd.read_csv(os.path.join(scen_dir, 'BESC_Bio_Natural_Gas.csv'))

csc_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_CSC', 'CSC_DAC_capacity.csv'))
csc_df['Scenario'] = scen
csc_process_df = pd.read_csv(os.path.join(scen_dir, 'CSC_capture.csv'))

csc_credit_df = pd.read_csv(os.path.join(scen_dir, dolphyn_results_folder, 'Results_CSC', 'CSC_DAC_capacity.csv'))
csc_credit_df['Scenario'] = scen
csc_credit_process_df = pd.read_csv(os.path.join(scen_dir, 'CSC_capture.csv'))

##########################################################################################################################################################

resource_abr = ['natural(?!.*ccs)', 'naturalgas_ccccsavgcf', 'nuclear', 'conventional_hydroelectric|small_hydroelectric', 'solar|pv', 'wind', 'H2', 'Bio|Gasification|Pyrolysis|FT']
resource_name = ['NG', 'NG CCS', 'Nuclear', 'Hydro', 'Solar', 'Wind', 'H2G2P', 'Bioenergy Credit']

for i in range(len(resource_abr)):
    df.loc[df['Resource'].str.contains(resource_abr[i], case=False, regex=True), 'Resource_Category'] = resource_name[i]

df['AnnualGeneration'] = df['AnnualGeneration'] * conversion_factor

aggregated_data = df.groupby(['Scenario', 'Resource_Category'])['AnnualGeneration'].sum().unstack().fillna(0)
aggregated_data = aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process SF Power data
sf_df['Resource_Category'] = 'Synthetic FT'

sf_merged_df = pd.merge(sf_df, sf_process_df[['Syn_Fuel_Resource', 'mwh_p_tonne_co2']],
                         left_on='Resource', right_on='Syn_Fuel_Resource', how='left')

sf_merged_df['Annual_Power_Consumption_EJ'] = (
    - sf_merged_df['Annual_CO2_Consumption'] * sf_merged_df['mwh_p_tonne_co2'] * conversion_factor
)

sf_aggregated_data = sf_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
sf_aggregated_data = sf_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process Syn NG Power data
syn_ng_df['Resource_Category'] = 'Synthetic NG'

syn_ng_merged_df = pd.merge(syn_ng_df, syn_ng_process_df[['Syn_NG_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_NG_Resource', how='left')

syn_ng_merged_df['Annual_Power_Consumption_EJ'] = (
    - syn_ng_merged_df['Annual_CO2_Consumption'] * syn_ng_merged_df['mwh_p_tonne_co2'] * conversion_factor
)

syn_ng_aggregated_data = syn_ng_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
syn_ng_aggregated_data = syn_ng_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process H2 electrolyzer Power data
hsc_df['Resource_Category'] = 'H2 Production'

hsc_merged_df = pd.merge(hsc_df, hsc_process_df[['H2_Resource', 'etaP2G']],
                          left_on='Resource', right_on='H2_Resource', how='left')

hsc_merged_df['Annual_Power_Consumption_EJ'] = (
    - hsc_merged_df['AnnualGeneration'] * hsc_merged_df['etaP2G'] * conversion_factor
)

hsc_aggregated_data = hsc_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
hsc_aggregated_data = hsc_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process DAC Power data
csc_df['Resource_Category'] = 'Sorbent DAC Input'

csc_merged_df = pd.merge(csc_df, csc_process_df[['CO2_Resource', 'etaPCO2_MWh_per_tonne']],
                          left_on='Resource', right_on='CO2_Resource', how='left')

csc_merged_df['Annual_Power_Consumption_EJ'] = (
    - csc_merged_df['Annual_Capture'] * csc_merged_df['etaPCO2_MWh_per_tonne'] * conversion_factor
)

csc_aggregated_data = csc_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
csc_aggregated_data = csc_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process DAC credit Power data
csc_credit_df['Resource_Category'] = 'Solvent DAC Power Credit'

csc_credit_merged_df = pd.merge(csc_credit_df, csc_credit_process_df[['CO2_Resource', 'Power_Production_MWh_per_tonne']],
                                 left_on='Resource', right_on='CO2_Resource', how='left')

csc_credit_merged_df['Annual_Power_Credit_EJ'] = (
    csc_credit_merged_df['Annual_Capture'] * csc_credit_merged_df['Power_Production_MWh_per_tonne'] * conversion_factor
)

csc_credit_aggregated_data = csc_credit_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Credit_EJ'].sum().unstack().fillna(0)
csc_credit_aggregated_data = csc_credit_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process Bio H2 Power data
bio_H2_df['Resource_Category'] = 'Bio H2 Input'

bio_H2_merged_df = pd.merge(bio_H2_df, bio_H2_process_df[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_H2_merged_df['Annual_Power_Consumption_EJ'] = (
    - bio_H2_merged_df['Annual_Biomass_Consumption'] * bio_H2_merged_df['Power_consumption_MWh_per_tonne'] * conversion_factor
)

bio_H2_aggregated_data = bio_H2_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
bio_H2_aggregated_data = bio_H2_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process Bio LF Power data
bio_LF_df['Resource_Category'] = 'Bio LF Input'

bio_LF_merged_df = pd.merge(bio_LF_df, bio_LF_process_df[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_LF_merged_df['Annual_Power_Consumption_EJ'] = (
    - bio_LF_merged_df['Annual_Biomass_Consumption'] * bio_LF_merged_df['Power_consumption_MWh_per_tonne'] * conversion_factor
)

bio_LF_aggregated_data = bio_LF_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
bio_LF_aggregated_data = bio_LF_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process Bio Electricity Power data
bio_Electricity_df['Resource_Category'] = 'Bio Electricity Input'

bio_Electricity_merged_df = pd.merge(bio_Electricity_df, bio_Electricity_process_df[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                                     left_on='Resource', right_on='Biorefinery', how='left')

bio_Electricity_merged_df['Annual_Power_Consumption_EJ'] = (
    - bio_Electricity_merged_df['Annual_Biomass_Consumption'] * bio_Electricity_merged_df['Power_consumption_MWh_per_tonne'] * conversion_factor
)

bio_Electricity_aggregated_data = bio_Electricity_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
bio_Electricity_aggregated_data = bio_Electricity_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

# Process Bio NG Power data
bio_NG_df['Resource_Category'] = 'Bio NG Input'

bio_NG_merged_df = pd.merge(bio_NG_df, bio_NG_process_df[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_NG_merged_df['Annual_Power_Consumption_EJ'] = (
    - bio_NG_merged_df['Annual_Biomass_Consumption'] * bio_NG_merged_df['Power_consumption_MWh_per_tonne'] * conversion_factor
)

bio_NG_aggregated_data = bio_NG_merged_df.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)
bio_NG_aggregated_data = bio_NG_aggregated_data.reindex(scenario_names).fillna(0)

##########################################################################################################################################################

demand_data = {scen: -Power_Demand_EJ}
demand_df = pd.DataFrame.from_dict(demand_data, orient='index', columns=['Demand'])

##########################################################################################################################################################
##########################################################################################################################################################

combined_data = pd.concat([aggregated_data, csc_credit_aggregated_data, hsc_aggregated_data, csc_aggregated_data, demand_df, sf_aggregated_data, syn_ng_aggregated_data, bio_H2_aggregated_data, bio_LF_aggregated_data, bio_Electricity_aggregated_data, bio_NG_aggregated_data], axis=1).fillna(0)

combine_mapping = {
    'Bioenergy Credit': 'Bioenergy Input',
    'Bio H2 Input': 'Bioenergy Input',
    'Bio LF Input': 'Bioenergy Input',
    'Bio Electricity Input': 'Bioenergy Input',
    'Bio NG Input': 'Bioenergy Input',
    'Solvent DAC Power Credit': 'NG CCS'
}

combined_data = combined_data.rename(columns=combine_mapping)
combined_data = combined_data.groupby(by=combined_data.columns, axis=1).sum()

desired_order = [
    'Demand',
    'H2 Production',
    'Sorbent DAC Input',
    'Bioenergy Input',
    'Synthetic FT',
    'Synthetic NG',
    'Hydro',
    'Nuclear',
    'NG',
    'NG CCS',
    'Solar',
    'Wind',
]

combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

category_colors = {
    'Hydro': 'blue',
    'Nuclear': 'red',
    'NG': 'lightgrey',
    'NG CCS': 'lightpink',
    'Solar': 'gold',
    'Wind': 'dodgerblue',
    'Sorbent DAC Input': 'darkblue',
    'Bioenergy Input': 'seagreen',
    'Synthetic NG': 'violet',
    'Synthetic FT': 'purple',
    'H2 Production': 'lightgreen',
    'Demand': 'bisque'
}

category_names = {
    'Demand': 'Demand',
    'H2 Production': 'Electrolyzer',
    'Synthetic FT': 'Syn. Liquids',
    'Synthetic NG': 'Syn. NG',
    'Bioenergy Input': 'Biofuel Prod.',
    'Sorbent DAC Input': 'Sorbent DAC',
    'Hydro': 'Hydro',
    'Nuclear': 'Nuclear',
    'NG': 'NG',
    'NG CCS': 'NG CCS',
    'Solar': 'Solar',
    'Wind': 'Wind',
}

plt.rcParams['font.family'] = 'Arial'

fig, ax = plt.subplots(figsize=(3.6, 2.2))
combined_data.plot(
    kind='barh', stacked=True, width=0.7, ax=ax,
    color=[category_colors[col] for col in combined_data.columns]
)

plt.ylabel('Scenario', fontsize=16)
plt.title('Electricity Balance (EJ)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)
ax.set_xlim(-50, 50)
ax.set_xticks([-40, -20, 0, 20, 40])
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in combined_data.columns]
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.2),
          ncol=2, fontsize=14, frameon=False)
#ax.legend().remove()
#plt.tight_layout()
# %%
#plt.show()
