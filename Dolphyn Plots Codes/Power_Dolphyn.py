import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import sys

# Set global option to display all columns
pd.set_option('display.max_columns', None)
scenario_names = ['HB-HS', 'HB-LS', 'LB-HS', 'LB-LS']

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir

##########################################################################################################################################################

# User-defined maximum available bioenergy for each scenario
Power_Demand_EJ = 20.79194776

##########################################################################################################################################################

##########################################################################################################################################################

# Load the Results files for multiple scenarios
file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/capacity_multi_sector.csv'
file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/capacity_multi_sector.csv'
file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/capacity_multi_sector.csv'
file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/capacity_multi_sector.csv'

df1 = pd.read_csv(file_path_1)
# %%
df2 = pd.read_csv(file_path_2)

df3 = pd.read_csv(file_path_3)
df4 = pd.read_csv(file_path_4)

# Add a column to identify scenarios in each DataFrame
df1['Scenario'] = 'HB-HS'
df2['Scenario'] = 'HB-LS'
df3['Scenario'] = 'LB-HS'
df4['Scenario'] = 'LB-LS'

##########################################################################################################################################################

# Load the Results sf_files for multiple scenarios
sf_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_LF/Synfuel_capacity.csv'
sf_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_LF/Synfuel_capacity.csv'
sf_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_LF/Synfuel_capacity.csv'
sf_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_LF/Synfuel_capacity.csv'

sf_df1 = pd.read_csv(sf_file_path_1)
sf_df2 = pd.read_csv(sf_file_path_2)
sf_df3 = pd.read_csv(sf_file_path_3)
sf_df4 = pd.read_csv(sf_file_path_4)

# Add a column to identify scenarios in each DataFrame
sf_df1['Scenario'] = 'HB-HS'
sf_df2['Scenario'] = 'HB-LS'
sf_df3['Scenario'] = 'LB-HS'
sf_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
sf_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/LFSC_Synfuel_Resources.csv'
sf_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/LFSC_Synfuel_Resources.csv'
sf_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/LFSC_Synfuel_Resources.csv'
sf_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/LFSC_Synfuel_Resources.csv'

sf_process_df1 = pd.read_csv(sf_process_parameters_path_1)
sf_process_df2 = pd.read_csv(sf_process_parameters_path_2)
sf_process_df3 = pd.read_csv(sf_process_parameters_path_3)
sf_process_df4 = pd.read_csv(sf_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results syn_ng_files for multiple scenarios
syn_ng_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_NG/Syn_ng_capacity.csv'
syn_ng_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_NG/Syn_ng_capacity.csv'
syn_ng_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_NG/Syn_ng_capacity.csv'
syn_ng_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_NG/Syn_ng_capacity.csv'

syn_ng_df1 = pd.read_csv(syn_ng_file_path_1)
syn_ng_df2 = pd.read_csv(syn_ng_file_path_2)
syn_ng_df3 = pd.read_csv(syn_ng_file_path_3)
syn_ng_df4 = pd.read_csv(syn_ng_file_path_4)

# Add a column to identify scenarios in each DataFrame
syn_ng_df1['Scenario'] = 'HB-HS'
syn_ng_df2['Scenario'] = 'HB-LS'
syn_ng_df3['Scenario'] = 'LB-HS'
syn_ng_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
syn_ng_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/NGSC_Syn_NG_Resources.csv'
syn_ng_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/NGSC_Syn_NG_Resources.csv'
syn_ng_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/NGSC_Syn_NG_Resources.csv'
syn_ng_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/NGSC_Syn_NG_Resources.csv'

syn_ng_process_df1 = pd.read_csv(syn_ng_process_parameters_path_1)
syn_ng_process_df2 = pd.read_csv(syn_ng_process_parameters_path_2)
syn_ng_process_df3 = pd.read_csv(syn_ng_process_parameters_path_3)
syn_ng_process_df4 = pd.read_csv(syn_ng_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results hsc_files for multiple scenarios
hsc_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_HSC/HSC_generation_storage_capacity.csv'
hsc_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_HSC/HSC_generation_storage_capacity.csv'
hsc_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_HSC/HSC_generation_storage_capacity.csv'
hsc_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_HSC/HSC_generation_storage_capacity.csv'

hsc_df1 = pd.read_csv(hsc_file_path_1)
hsc_df2 = pd.read_csv(hsc_file_path_2)
hsc_df3 = pd.read_csv(hsc_file_path_3)
hsc_df4 = pd.read_csv(hsc_file_path_4)

# Add a column to identify scenarios in each DataFrame
hsc_df1['Scenario'] = 'HB-HS'
hsc_df2['Scenario'] = 'HB-LS'
hsc_df3['Scenario'] = 'LB-HS'
hsc_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
hsc_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/HSC_generation.csv'
hsc_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/HSC_generation.csv'
hsc_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/HSC_generation.csv'
hsc_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/HSC_generation.csv'

hsc_process_df1 = pd.read_csv(hsc_process_parameters_path_1)
hsc_process_df2 = pd.read_csv(hsc_process_parameters_path_2)
hsc_process_df3 = pd.read_csv(hsc_process_parameters_path_3)
hsc_process_df4 = pd.read_csv(hsc_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results bio_LF_files for multiple scenarios
bio_LF_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_LF_capacity.csv'
bio_LF_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_LF_capacity.csv'
bio_LF_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_LF_capacity.csv'
bio_LF_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_LF_capacity.csv'

bio_LF_df1 = pd.read_csv(bio_LF_file_path_1)
bio_LF_df2 = pd.read_csv(bio_LF_file_path_2)
bio_LF_df3 = pd.read_csv(bio_LF_file_path_3)
bio_LF_df4 = pd.read_csv(bio_LF_file_path_4)

# Add a column to identify scenarios in each DataFrame
bio_LF_df1['Scenario'] = 'HB-HS'
bio_LF_df2['Scenario'] = 'HB-LS'
bio_LF_df3['Scenario'] = 'LB-HS'
bio_LF_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
bio_LF_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/BESC_Bio_Liquid_Fuels.csv'
bio_LF_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/BESC_Bio_Liquid_Fuels.csv'
bio_LF_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/BESC_Bio_Liquid_Fuels.csv'
bio_LF_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/BESC_Bio_Liquid_Fuels.csv'

bio_LF_process_df1 = pd.read_csv(bio_LF_process_parameters_path_1)
bio_LF_process_df2 = pd.read_csv(bio_LF_process_parameters_path_2)
bio_LF_process_df3 = pd.read_csv(bio_LF_process_parameters_path_3)
bio_LF_process_df4 = pd.read_csv(bio_LF_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results bio_H2_files for multiple scenarios
bio_H2_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_H2_capacity.csv'
bio_H2_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_H2_capacity.csv'
bio_H2_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_H2_capacity.csv'
bio_H2_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_H2_capacity.csv'

bio_H2_df1 = pd.read_csv(bio_H2_file_path_1)
bio_H2_df2 = pd.read_csv(bio_H2_file_path_2)
bio_H2_df3 = pd.read_csv(bio_H2_file_path_3)
bio_H2_df4 = pd.read_csv(bio_H2_file_path_4)

# Add a column to identify scenarios in each DataFrame
bio_H2_df1['Scenario'] = 'HB-HS'
bio_H2_df2['Scenario'] = 'HB-LS'
bio_H2_df3['Scenario'] = 'LB-HS'
bio_H2_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
bio_H2_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/BESC_Bio_H2.csv'
bio_H2_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/BESC_Bio_H2.csv'
bio_H2_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/BESC_Bio_H2.csv'
bio_H2_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/BESC_Bio_H2.csv'

bio_H2_process_df1 = pd.read_csv(bio_H2_process_parameters_path_1)
bio_H2_process_df2 = pd.read_csv(bio_H2_process_parameters_path_2)
bio_H2_process_df3 = pd.read_csv(bio_H2_process_parameters_path_3)
bio_H2_process_df4 = pd.read_csv(bio_H2_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results bio_Electricity_files for multiple scenarios
bio_Electricity_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_Electricity_capacity.csv'
bio_Electricity_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_Electricity_capacity.csv'
bio_Electricity_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_Electricity_capacity.csv'
bio_Electricity_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_Electricity_capacity.csv'

bio_Electricity_df1 = pd.read_csv(bio_Electricity_file_path_1)
bio_Electricity_df2 = pd.read_csv(bio_Electricity_file_path_2)
bio_Electricity_df3 = pd.read_csv(bio_Electricity_file_path_3)
bio_Electricity_df4 = pd.read_csv(bio_Electricity_file_path_4)

# Add a column to identify scenarios in each DataFrame
bio_Electricity_df1['Scenario'] = 'HB-HS'
bio_Electricity_df2['Scenario'] = 'HB-LS'
bio_Electricity_df3['Scenario'] = 'LB-HS'
bio_Electricity_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
bio_Electricity_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/BESC_Bio_Electricity.csv'
bio_Electricity_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/BESC_Bio_Electricity.csv'
bio_Electricity_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/BESC_Bio_Electricity.csv'
bio_Electricity_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/BESC_Bio_Electricity.csv'

bio_Electricity_process_df1 = pd.read_csv(bio_Electricity_process_parameters_path_1)
bio_Electricity_process_df2 = pd.read_csv(bio_Electricity_process_parameters_path_2)
bio_Electricity_process_df3 = pd.read_csv(bio_Electricity_process_parameters_path_3)
bio_Electricity_process_df4 = pd.read_csv(bio_Electricity_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results bio_NG_files for multiple scenarios
bio_NG_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_NG_capacity.csv'
bio_NG_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_NG_capacity.csv'
bio_NG_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_BESC/BESC_Bio_NG_capacity.csv'
bio_NG_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_BESC/BESC_Bio_NG_capacity.csv'

bio_NG_df1 = pd.read_csv(bio_NG_file_path_1)
bio_NG_df2 = pd.read_csv(bio_NG_file_path_2)
bio_NG_df3 = pd.read_csv(bio_NG_file_path_3)
bio_NG_df4 = pd.read_csv(bio_NG_file_path_4)

# Add a column to identify scenarios in each DataFrame
bio_NG_df1['Scenario'] = 'HB-HS'
bio_NG_df2['Scenario'] = 'HB-LS'
bio_NG_df3['Scenario'] = 'LB-HS'
bio_NG_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
bio_NG_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/BESC_Bio_Natural_Gas.csv'
bio_NG_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/BESC_Bio_Natural_Gas.csv'
bio_NG_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/BESC_Bio_Natural_Gas.csv'
bio_NG_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/BESC_Bio_Natural_Gas.csv'

bio_NG_process_df1 = pd.read_csv(bio_NG_process_parameters_path_1)
bio_NG_process_df2 = pd.read_csv(bio_NG_process_parameters_path_2)
bio_NG_process_df3 = pd.read_csv(bio_NG_process_parameters_path_3)
bio_NG_process_df4 = pd.read_csv(bio_NG_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results csc_files for multiple scenarios
csc_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'

csc_df1 = pd.read_csv(csc_file_path_1)
csc_df2 = pd.read_csv(csc_file_path_2)
csc_df3 = pd.read_csv(csc_file_path_3)
csc_df4 = pd.read_csv(csc_file_path_4)

# Add a column to identify scenarios in each DataFrame
csc_df1['Scenario'] = 'HB-HS'
csc_df2['Scenario'] = 'HB-LS'
csc_df3['Scenario'] = 'LB-HS'
csc_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
csc_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/CSC_capture.csv'
csc_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/CSC_capture.csv'
csc_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/CSC_capture.csv'
csc_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/CSC_capture.csv'

csc_process_df1 = pd.read_csv(csc_process_parameters_path_1)
csc_process_df2 = pd.read_csv(csc_process_parameters_path_2)
csc_process_df3 = pd.read_csv(csc_process_parameters_path_3)
csc_process_df4 = pd.read_csv(csc_process_parameters_path_4)

##########################################################################################################################################################

# Load the Results csc_credit_files for multiple scenarios
csc_credit_file_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_credit_file_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_credit_file_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'
csc_credit_file_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/Results/Results_CSC/CSC_DAC_capacity.csv'

csc_credit_df1 = pd.read_csv(csc_credit_file_path_1)
csc_credit_df2 = pd.read_csv(csc_credit_file_path_2)
csc_credit_df3 = pd.read_csv(csc_credit_file_path_3)
csc_credit_df4 = pd.read_csv(csc_credit_file_path_4)

# Add a column to identify scenarios in each DataFrame
csc_credit_df1['Scenario'] = 'HB-HS'
csc_credit_df2['Scenario'] = 'HB-LS'
csc_credit_df3['Scenario'] = 'LB-HS'
csc_credit_df4['Scenario'] = 'LB-LS'

# Load the Process_Parameters file (assuming it contains scenario-specific parameters)
csc_credit_process_parameters_path_1 = f'{dolphyn_base_dir}/NineZones_High_Biomass_High_CO2/CSC_capture.csv'
csc_credit_process_parameters_path_2 = f'{dolphyn_base_dir}/NineZones_High_Biomass_Low_CO2/CSC_capture.csv'
csc_credit_process_parameters_path_3 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_High_CO2/CSC_capture.csv'
csc_credit_process_parameters_path_4 = f'{dolphyn_base_dir}/NineZones_Low_Biomass_Low_CO2/CSC_capture.csv'

csc_credit_process_df1 = pd.read_csv(csc_credit_process_parameters_path_1)
csc_credit_process_df2 = pd.read_csv(csc_credit_process_parameters_path_2)
csc_credit_process_df3 = pd.read_csv(csc_credit_process_parameters_path_3)
csc_credit_process_df4 = pd.read_csv(csc_credit_process_parameters_path_4)

##########################################################################################################################################################

# Combine both Results DataFrames
df_combined = pd.concat([df1, df2, df3, df4], ignore_index=True)
sf_df_combined = pd.concat([sf_df1, sf_df2, sf_df3, sf_df4], ignore_index=True)
syn_ng_df_combined = pd.concat([syn_ng_df1, syn_ng_df2, syn_ng_df3, syn_ng_df4], ignore_index=True)
hsc_df_combined = pd.concat([hsc_df1, hsc_df2, hsc_df3, hsc_df4], ignore_index=True)
bio_LF_df_combined = pd.concat([bio_LF_df1, bio_LF_df2, bio_LF_df3, bio_LF_df4], ignore_index=True)
bio_H2_df_combined = pd.concat([bio_H2_df1, bio_H2_df2, bio_H2_df3, bio_H2_df4], ignore_index=True)
bio_Electricity_df_combined = pd.concat([bio_Electricity_df1, bio_Electricity_df2, bio_Electricity_df3, bio_Electricity_df4], ignore_index=True)
bio_NG_df_combined = pd.concat([bio_NG_df1, bio_NG_df2, bio_NG_df3, bio_NG_df4], ignore_index=True)
csc_df_combined = pd.concat([csc_df1, csc_df2, csc_df3, csc_df4], ignore_index=True)
csc_credit_df_combined = pd.concat([csc_credit_df1, csc_credit_df2, csc_credit_df3, csc_credit_df4], ignore_index=True)

##########################################################################################################################################################


resource_abr = ['natural(?!.*ccs)', 'naturalgas_ccccsavgcf', 'nuclear', 'conventional_hydroelectric|small_hydroelectric', 'solar|pv', 'wind', 'H2', 'Bio|Gasification|Pyrolysis|FT']
resource_name = ['NG', 'NG CCS', 'Nuclear', 'Hydro', 'Solar', 'Wind', 'H2G2P', 'Bioenergy Credit']

# Create a new column 'Resource_Category' based on matching criteria
for i in range(len(resource_abr)):
    df_combined.loc[df_combined['Resource'].str.contains(resource_abr[i], case=False, regex=True), 'Resource_Category'] = resource_name[i]


# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" with a conversion factor if needed
conversion_factor = 3.6e-9  # Adjust as necessary

df_combined['AnnualGeneration'] = (df_combined['AnnualGeneration'] * conversion_factor)

# Aggregating the new column by Scenario and Resource_Category
aggregated_data = df_combined.groupby(['Scenario', 'Resource_Category'])['AnnualGeneration'].sum().unstack().fillna(0)


##########################################################################################################################################################

# Process SF Power data
sf_df_combined['Resource_Category'] = 'Synthetic FT'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
sf_scenario_1 = sf_df_combined[sf_df_combined['Scenario'] == 'HB-HS']
sf_scenario_2 = sf_df_combined[sf_df_combined['Scenario'] == 'HB-LS']
sf_scenario_3 = sf_df_combined[sf_df_combined['Scenario'] == 'LB-HS']
sf_scenario_4 = sf_df_combined[sf_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
sf_merged_df1 = pd.merge(sf_scenario_1, sf_process_df1[['Syn_Fuel_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_Fuel_Resource', how='left')

sf_merged_df2 = pd.merge(sf_scenario_2, sf_process_df2[['Syn_Fuel_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_Fuel_Resource', how='left')

sf_merged_df3 = pd.merge(sf_scenario_3, sf_process_df3[['Syn_Fuel_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_Fuel_Resource', how='left')

sf_merged_df4 = pd.merge(sf_scenario_4, sf_process_df4[['Syn_Fuel_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_Fuel_Resource', how='left')


# Combine merged DataFrames for Bio H2
sf_merged_combined = pd.concat([sf_merged_df1, sf_merged_df2, sf_merged_df3, sf_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
sf_merged_combined['Annual_Power_Consumption_EJ'] = (
    - sf_merged_combined['Annual_CO2_Consumption'] * sf_merged_combined['mwh_p_tonne_co2'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
sf_aggregated_data = sf_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process Syn NG Power data
syn_ng_df_combined['Resource_Category'] = 'Synthetic NG'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
syn_ng_scenario_1 = syn_ng_df_combined[syn_ng_df_combined['Scenario'] == 'HB-HS']
syn_ng_scenario_2 = syn_ng_df_combined[syn_ng_df_combined['Scenario'] == 'HB-LS']
syn_ng_scenario_3 = syn_ng_df_combined[syn_ng_df_combined['Scenario'] == 'LB-HS']
syn_ng_scenario_4 = syn_ng_df_combined[syn_ng_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
syn_ng_merged_df1 = pd.merge(syn_ng_scenario_1, syn_ng_process_df1[['Syn_NG_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_NG_Resource', how='left')

syn_ng_merged_df2 = pd.merge(syn_ng_scenario_2, syn_ng_process_df2[['Syn_NG_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_NG_Resource', how='left')

syn_ng_merged_df3 = pd.merge(syn_ng_scenario_3, syn_ng_process_df3[['Syn_NG_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_NG_Resource', how='left')

syn_ng_merged_df4 = pd.merge(syn_ng_scenario_4, syn_ng_process_df4[['Syn_NG_Resource', 'mwh_p_tonne_co2']],
                             left_on='Resource', right_on='Syn_NG_Resource', how='left')


# Combine merged DataFrames for Bio H2
syn_ng_merged_combined = pd.concat([syn_ng_merged_df1, syn_ng_merged_df2, syn_ng_merged_df3, syn_ng_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
syn_ng_merged_combined['Annual_Power_Consumption_EJ'] = (
    - syn_ng_merged_combined['Annual_CO2_Consumption'] * syn_ng_merged_combined['mwh_p_tonne_co2'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
syn_ng_aggregated_data = syn_ng_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process SF Power data
hsc_df_combined['Resource_Category'] = 'H2 Production'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
hsc_scenario_1 = hsc_df_combined[hsc_df_combined['Scenario'] == 'HB-HS']
hsc_scenario_2 = hsc_df_combined[hsc_df_combined['Scenario'] == 'HB-LS']
hsc_scenario_3 = hsc_df_combined[hsc_df_combined['Scenario'] == 'LB-HS']
hsc_scenario_4 = hsc_df_combined[hsc_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
hsc_merged_df1 = pd.merge(hsc_scenario_1, hsc_process_df1[['H2_Resource', 'etaP2G']],
                             left_on='Resource', right_on='H2_Resource', how='left')

hsc_merged_df2 = pd.merge(hsc_scenario_2, hsc_process_df2[['H2_Resource', 'etaP2G']],
                             left_on='Resource', right_on='H2_Resource', how='left')

hsc_merged_df3 = pd.merge(hsc_scenario_3, hsc_process_df3[['H2_Resource', 'etaP2G']],
                             left_on='Resource', right_on='H2_Resource', how='left')

hsc_merged_df4 = pd.merge(hsc_scenario_4, hsc_process_df4[['H2_Resource', 'etaP2G']],
                             left_on='Resource', right_on='H2_Resource', how='left')


# Combine merged DataFrames for Bio H2
hsc_merged_combined = pd.concat([hsc_merged_df1, hsc_merged_df2, hsc_merged_df3, hsc_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
hsc_merged_combined['Annual_Power_Consumption_EJ'] = (
    - hsc_merged_combined['AnnualGeneration'] * hsc_merged_combined['etaP2G'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
hsc_aggregated_data = hsc_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process DAC Power data
csc_df_combined['Resource_Category'] = 'Sorbent DAC Input'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
csc_scenario_1 = csc_df_combined[csc_df_combined['Scenario'] == 'HB-HS']
csc_scenario_2 = csc_df_combined[csc_df_combined['Scenario'] == 'HB-LS']
csc_scenario_3 = csc_df_combined[csc_df_combined['Scenario'] == 'LB-HS']
csc_scenario_4 = csc_df_combined[csc_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
csc_merged_df1 = pd.merge(csc_scenario_1, csc_process_df1[['CO2_Resource', 'etaPCO2_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_merged_df2 = pd.merge(csc_scenario_2, csc_process_df2[['CO2_Resource', 'etaPCO2_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_merged_df3 = pd.merge(csc_scenario_3, csc_process_df3[['CO2_Resource', 'etaPCO2_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_merged_df4 = pd.merge(csc_scenario_4, csc_process_df4[['CO2_Resource', 'etaPCO2_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')


# Combine merged DataFrames for Bio H2
csc_merged_combined = pd.concat([csc_merged_df1, csc_merged_df2, csc_merged_df3, csc_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
csc_merged_combined['Annual_Power_Consumption_EJ'] = (
    - csc_merged_combined['Annual_Capture'] * csc_merged_combined['etaPCO2_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
csc_aggregated_data = csc_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process DAC credit Power data
csc_credit_df_combined['Resource_Category'] = 'Solvent DAC Power Credit'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
csc_credit_scenario_1 = csc_credit_df_combined[csc_credit_df_combined['Scenario'] == 'HB-HS']
csc_credit_scenario_2 = csc_credit_df_combined[csc_credit_df_combined['Scenario'] == 'HB-LS']
csc_credit_scenario_3 = csc_credit_df_combined[csc_credit_df_combined['Scenario'] == 'LB-HS']
csc_credit_scenario_4 = csc_credit_df_combined[csc_credit_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
csc_credit_merged_df1 = pd.merge(csc_credit_scenario_1, csc_credit_process_df1[['CO2_Resource', 'Power_Production_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_credit_merged_df2 = pd.merge(csc_credit_scenario_2, csc_credit_process_df2[['CO2_Resource', 'Power_Production_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_credit_merged_df3 = pd.merge(csc_credit_scenario_3, csc_credit_process_df3[['CO2_Resource', 'Power_Production_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')

csc_credit_merged_df4 = pd.merge(csc_credit_scenario_4, csc_credit_process_df4[['CO2_Resource', 'Power_Production_MWh_per_tonne']],
                             left_on='Resource', right_on='CO2_Resource', how='left')


# Combine merged DataFrames for Bio H2
csc_credit_merged_combined = pd.concat([csc_credit_merged_df1, csc_credit_merged_df2, csc_credit_merged_df3, csc_credit_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
csc_credit_merged_combined['Annual_Power_Credit_EJ'] = (
    csc_credit_merged_combined['Annual_Capture'] * csc_credit_merged_combined['Power_Production_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
csc_credit_aggregated_data = csc_credit_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Credit_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process Bio H2 Power data
bio_H2_df_combined['Resource_Category'] = 'Bio H2 Input'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio H2
bio_H2_scenario_1 = bio_H2_df_combined[bio_H2_df_combined['Scenario'] == 'HB-HS']
bio_H2_scenario_2 = bio_H2_df_combined[bio_H2_df_combined['Scenario'] == 'HB-LS']
bio_H2_scenario_3 = bio_H2_df_combined[bio_H2_df_combined['Scenario'] == 'LB-HS']
bio_H2_scenario_4 = bio_H2_df_combined[bio_H2_df_combined['Scenario'] == 'LB-LS']

# Merge Bio H2 data with corresponding Process Parameters
bio_H2_merged_df1 = pd.merge(bio_H2_scenario_1, bio_H2_process_df1[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_H2_merged_df2 = pd.merge(bio_H2_scenario_2, bio_H2_process_df2[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_H2_merged_df3 = pd.merge(bio_H2_scenario_3, bio_H2_process_df3[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_H2_merged_df4 = pd.merge(bio_H2_scenario_4, bio_H2_process_df4[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')


# Combine merged DataFrames for Bio H2
bio_H2_merged_combined = pd.concat([bio_H2_merged_df1, bio_H2_merged_df2, bio_H2_merged_df3, bio_H2_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio H2
bio_H2_merged_combined['Annual_Power_Consumption_EJ'] = (
    - bio_H2_merged_combined['Annual_Biomass_Consumption'] * bio_H2_merged_combined['Power_consumption_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio H2
bio_H2_aggregated_data = bio_H2_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)


##########################################################################################################################################################

# Process DAC Power data
bio_LF_df_combined['Resource_Category'] = 'Bio LF Input'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio LF
bio_LF_scenario_1 = bio_LF_df_combined[bio_LF_df_combined['Scenario'] == 'HB-HS']
bio_LF_scenario_2 = bio_LF_df_combined[bio_LF_df_combined['Scenario'] == 'HB-LS']
bio_LF_scenario_3 = bio_LF_df_combined[bio_LF_df_combined['Scenario'] == 'LB-HS']
bio_LF_scenario_4 = bio_LF_df_combined[bio_LF_df_combined['Scenario'] == 'LB-LS']

# Merge Bio LF data with corresponding Process Parameters
bio_LF_merged_df1 = pd.merge(bio_LF_scenario_1, bio_LF_process_df1[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_LF_merged_df2 = pd.merge(bio_LF_scenario_2, bio_LF_process_df2[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_LF_merged_df3 = pd.merge(bio_LF_scenario_3, bio_LF_process_df3[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_LF_merged_df4 = pd.merge(bio_LF_scenario_4, bio_LF_process_df4[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')


# Combine merged DataFrames for Bio LF
bio_LF_merged_combined = pd.concat([bio_LF_merged_df1, bio_LF_merged_df2, bio_LF_merged_df3, bio_LF_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio LF
bio_LF_merged_combined['Annual_Power_Consumption_EJ'] = (
    - bio_LF_merged_combined['Annual_Biomass_Consumption'] * bio_LF_merged_combined['Power_consumption_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio LF
bio_LF_aggregated_data = bio_LF_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process Bio Electricity Power data
bio_Electricity_df_combined['Resource_Category'] = 'Bio Electricity Input'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio Electricity
bio_Electricity_scenario_1 = bio_Electricity_df_combined[bio_Electricity_df_combined['Scenario'] == 'HB-HS']
bio_Electricity_scenario_2 = bio_Electricity_df_combined[bio_Electricity_df_combined['Scenario'] == 'HB-LS']
bio_Electricity_scenario_3 = bio_Electricity_df_combined[bio_Electricity_df_combined['Scenario'] == 'LB-HS']
bio_Electricity_scenario_4 = bio_Electricity_df_combined[bio_Electricity_df_combined['Scenario'] == 'LB-LS']

# Merge Bio Electricity data with corresponding Process Parameters
bio_Electricity_merged_df1 = pd.merge(bio_Electricity_scenario_1, bio_Electricity_process_df1[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_Electricity_merged_df2 = pd.merge(bio_Electricity_scenario_2, bio_Electricity_process_df2[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_Electricity_merged_df3 = pd.merge(bio_Electricity_scenario_3, bio_Electricity_process_df3[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_Electricity_merged_df4 = pd.merge(bio_Electricity_scenario_4, bio_Electricity_process_df4[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')


# Combine merged DataFrames for Bio Electricity
bio_Electricity_merged_combined = pd.concat([bio_Electricity_merged_df1, bio_Electricity_merged_df2, bio_Electricity_merged_df3, bio_Electricity_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio Electricity
bio_Electricity_merged_combined['Annual_Power_Consumption_EJ'] = (
    - bio_Electricity_merged_combined['Annual_Biomass_Consumption'] * bio_Electricity_merged_combined['Power_consumption_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio Electricity
bio_Electricity_aggregated_data = bio_Electricity_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Process Bio NG Power data
bio_NG_df_combined['Resource_Category'] = 'Bio NG Input'  # Setting a fixed category for simplicity

# Separate data by scenario for Bio NG
bio_NG_scenario_1 = bio_NG_df_combined[bio_NG_df_combined['Scenario'] == 'HB-HS']
bio_NG_scenario_2 = bio_NG_df_combined[bio_NG_df_combined['Scenario'] == 'HB-LS']
bio_NG_scenario_3 = bio_NG_df_combined[bio_NG_df_combined['Scenario'] == 'LB-HS']
bio_NG_scenario_4 = bio_NG_df_combined[bio_NG_df_combined['Scenario'] == 'LB-LS']

# Merge Bio NG data with corresponding Process Parameters
bio_NG_merged_df1 = pd.merge(bio_NG_scenario_1, bio_NG_process_df1[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_NG_merged_df2 = pd.merge(bio_NG_scenario_2, bio_NG_process_df2[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_NG_merged_df3 = pd.merge(bio_NG_scenario_3, bio_NG_process_df3[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')

bio_NG_merged_df4 = pd.merge(bio_NG_scenario_4, bio_NG_process_df4[['Biorefinery', 'Power_consumption_MWh_per_tonne']],
                             left_on='Resource', right_on='Biorefinery', how='left')


# Combine merged DataFrames for Bio NG
bio_NG_merged_combined = pd.concat([bio_NG_merged_df1, bio_NG_merged_df2, bio_NG_merged_df3, bio_NG_merged_df4], ignore_index=True)

# Calculate the new column "Annual_Bioenergy_Consumption_MMBtu" for Bio NG
bio_NG_merged_combined['Annual_Power_Consumption_EJ'] = (
    - bio_NG_merged_combined['Annual_Biomass_Consumption'] * bio_NG_merged_combined['Power_consumption_MWh_per_tonne'] * conversion_factor
)

# Aggregating the new column by Scenario and Resource_Category for Bio NG
bio_NG_aggregated_data = bio_NG_merged_combined.groupby(['Scenario', 'Resource_Category'])['Annual_Power_Consumption_EJ'].sum().unstack().fillna(0)

##########################################################################################################################################################

# Example demand data for each scenario (replace with your actual demand data)
demand_data = {
    'HB-HS': -Power_Demand_EJ,  # Example values, adjust accordingly
    'HB-LS': -Power_Demand_EJ,
    'LB-HS': -Power_Demand_EJ,
    'LB-LS': -Power_Demand_EJ
}

# Convert demand data to a DataFrame
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

# Apply the mapping to combine categories in the columns
combined_data = combined_data.rename(columns=combine_mapping)

# Group the combined data by the new category names and sum the values
combined_data = combined_data.groupby(by=combined_data.columns, axis=1).sum()


# Custom order for arranging categories
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

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

# Custom colors and display names
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
    'Demand':'Demand',
    'H2 Production':'Electrolyzer',
    'Synthetic FT':'Syn. Liquids',
    'Synthetic NG':'Syn. NG',
    'Bioenergy Input':'Biofuel Prod.',
    'Sorbent DAC Input': 'Sorbent DAC',
    'Hydro':'Hydro',
    'Nuclear':'Nuclear',
    'NG':'NG',
    'NG CCS':'NG CCS',
    'Solar':'Solar',
    'Wind':'Wind',
}

plt.rcParams['font.family'] = 'Arial'

# Plotting the combined stacked horizontal bar chart
fig, ax = plt.subplots(figsize=(3.6, 2.2))
combined_data.plot(
    kind='barh', stacked=True, width=0.7, ax=ax,
    color=[category_colors[col] for col in desired_order]
)

plt.ylabel('Scenario', fontsize=16)
plt.title('Electricity Balance (EJ)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)
ax.set_xlim(-50, 50)
ax.set_xticks([-40, -20, 0, 20, 40])
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

# Add custom legend with 3 rows (12 items → ncol=4)
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in desired_order]
ax.legend(handles, custom_labels, loc='upper center', bbox_to_anchor=(0.5, -0.2),
          ncol=2, fontsize=14, frameon=False)
#ax.legend().remove()
#plt.tight_layout()
# %%
#plt.show()
