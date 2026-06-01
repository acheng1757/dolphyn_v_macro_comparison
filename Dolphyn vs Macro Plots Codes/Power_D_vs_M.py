import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir, macro_results_folder,
    dolphyn_results_folder, scenario_names,
)

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ

dolphyn_scenario_paths = {
    scenario_names[0]: f"all_demand_test/{dolphyn_results_folder}",
}

macro_scenario_paths = {
    scenario_names[0]: f"clean_slate_5_25/{macro_results_folder}/results",
}

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def read_scenario_csvs(relative_path):
    """
    Read one CSV with the same relative path from each Dolphyn scenario folder.
    Adds a Scenario column and returns a combined dataframe plus a scenario dict.
    """
    scenario_dfs = {}

    for scen, scen_folder in dolphyn_scenario_paths.items():
        path = os.path.join(dolphyn_base_dir, scen_folder, relative_path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found for {scen}: {path}")

        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        df["Scenario"] = scen
        scenario_dfs[scen] = df

    combined = pd.concat(
        [scenario_dfs[scen] for scen in scenario_names],
        ignore_index=True,
    )

    return combined, scenario_dfs


def read_process_csvs(relative_path):
    """
    Read one process-parameter CSV with the same relative path from each
    Dolphyn scenario folder.
    """
    scenario_dfs = {}

    for scen, scen_folder in dolphyn_scenario_paths.items():
        path = os.path.join(dolphyn_base_dir, scen_folder, relative_path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Process file not found for {scen}: {path}")

        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        scenario_dfs[scen] = df

    return scenario_dfs


def aggregate_by_scenario_category(df, value_col):
    """
    Aggregate a dataframe by Scenario and Resource_Category.
    """
    return (
        df.groupby(["Scenario", "Resource_Category"])[value_col]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )


def merge_scenario_process_data(
    result_df,
    process_dfs,
    result_key,
    process_key,
    process_cols,
):
    """
    Merge result data with scenario-specific process-parameter data.
    """
    merged_tables = []

    for scen in scenario_names:
        result_scen = result_df[result_df["Scenario"] == scen].copy()
        process_scen = process_dfs[scen][[process_key] + process_cols].copy()

        merged = pd.merge(
            result_scen,
            process_scen,
            left_on=result_key,
            right_on=process_key,
            how="left",
        )

        merged_tables.append(merged)

    return pd.concat(merged_tables, ignore_index=True)


def read_time_weights(time_weights_path):
    """
    Read Dolphyn time_weights.csv and return a 1-D Series of hourly weights.
    Written flexibly because different Dolphyn outputs may name the weight
    column differently.
    """
    weights_df = pd.read_csv(time_weights_path)
    weights_df.columns = weights_df.columns.str.strip()

    possible_weight_cols = [
        "Weight",
        "Weights",
        "weight",
        "weights",
        "time_weight",
        "Time_Weight",
        "Sub_Weights",
        "TimeWeights",
        "Rep_Period_Weight",
    ]

    weight_col = next(
        (c for c in possible_weight_cols if c in weights_df.columns),
        None,
    )

    if weight_col is None:
        numeric_cols = weights_df.select_dtypes(include="number").columns.tolist()

        # Avoid using obvious time/index columns as weights when possible.
        numeric_cols_no_index = [
            c for c in numeric_cols
            if c.lower() not in ["time_index", "time", "hour", "hours", "index"]
        ]

        if len(numeric_cols_no_index) == 1:
            weight_col = numeric_cols_no_index[0]
        elif len(numeric_cols) == 1:
            weight_col = numeric_cols[0]
        else:
            raise ValueError(
                f"Could not identify the weight column in {time_weights_path}. "
                f"Available columns are: {weights_df.columns.tolist()}"
            )

    return pd.to_numeric(weights_df[weight_col], errors="coerce").fillna(0.0)


def compute_dolphyn_power_demand_ej(scenario_dir):
    """
    Compute total weighted electricity demand for one Dolphyn scenario.

    Assumes:
      - Load_data.csv is in TDR_Results/
      - time_weights.csv is in Results/
      - load columns are named Load_MW_z1, Load_MW_z2, ...
      - hourly demand MW * time weight gives MWh
    """
    load_path = os.path.join(scenario_dir, "TDR_Results", "Load_data.csv")
    time_weights_path = os.path.join(scenario_dir, "Results", "time_weights.csv")

    if not os.path.exists(load_path):
        raise FileNotFoundError(f"Load_data.csv not found: {load_path}")

    if not os.path.exists(time_weights_path):
        raise FileNotFoundError(f"time_weights.csv not found: {time_weights_path}")

    load_df = pd.read_csv(load_path)
    load_df.columns = load_df.columns.str.strip()

    load_cols = [
        c for c in load_df.columns
        if c.lower().startswith("load_mw")
    ]

    if not load_cols:
        raise ValueError(
            f"No Load_MW* columns found in {load_path}. "
            f"Available columns are: {load_df.columns.tolist()}"
        )

    hourly_global_load_mw = (
        load_df[load_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .sum(axis=1)
    )

    time_weights = read_time_weights(time_weights_path)

    if len(time_weights) != len(hourly_global_load_mw):
        raise ValueError(
            f"Length mismatch for {scenario_dir}: "
            f"{len(hourly_global_load_mw)} hourly load rows but "
            f"{len(time_weights)} time weights."
        )

    total_demand_mwh = (hourly_global_load_mw * time_weights).sum()
    total_demand_ej = total_demand_mwh * MWH_TO_EJ

    return total_demand_ej


def map_macro_power_category(row):
    """
    Map MACRO annual_flows_balance_Power.csv rows to the same plotting
    categories used for Dolphyn.

    Small MACRO-only categories are intentionally excluded:
      - transmission losses
      - storage losses
      - H2 turbines
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Demand rows
    if sector == "Demand":
        return "Demand"

    # Power generation technologies
    if sector == "Power":
        if category in ["Hydro", "Nuclear", "NG", "NG CCS", "Solar", "Wind"]:
            return category

        # Exclude small MACRO-only categories from the plot
        if category in ["Battery", "H2 CCGT", "H2 OCGT"]:
            return None

        return None

    # Hydrogen-sector electricity consumption
    if sector == "Hydrogen":
        return "H2 Production"

    # CO2-sector electricity consumption
    if sector == "CO2":
        return "Sorbent DAC Input"

    # Bioenergy electricity consumption or credit
    if sector == "Bioenergy":
        return "Bioenergy Input"

    if sector == "Ethanol":
        return "Ethanol Input"

    if sector == "Ethylene":
        return "Ethylene Input"

    # Synthetic fuels
    if sector == "Synthetic fuels":
        if category == "S-NG":
            return "Synthetic NG"
        if category in ["S-J", "S-J-CC99", "S-J-99"]:
            return "Synthetic FT"
        return "Synthetic FT"

    # Exclude transmission losses
    if sector == "Transmission":
        return None

    return None


# ---------------------------------------------------------------------
# Load Dolphyn result files
# ---------------------------------------------------------------------

df_combined, _ = read_scenario_csvs("Results/capacity_multi_sector.csv")

sf_df_combined, _ = read_scenario_csvs("Results/Results_LF/Synfuel_capacity.csv")
syn_ng_df_combined, _ = read_scenario_csvs("Results/Results_NG/Syn_ng_capacity.csv")
hsc_df_combined, _ = read_scenario_csvs("Results/Results_HSC/HSC_generation_storage_capacity.csv")

bio_LF_df_combined, _ = read_scenario_csvs("Results/Results_BESC/BESC_Bio_LF_capacity.csv")
bio_H2_df_combined, _ = read_scenario_csvs("Results/Results_BESC/BESC_Bio_H2_capacity.csv")
bio_Electricity_df_combined, _ = read_scenario_csvs("Results/Results_BESC/BESC_Bio_Electricity_capacity.csv")
bio_NG_df_combined, _ = read_scenario_csvs("Results/Results_BESC/BESC_Bio_NG_capacity.csv")

csc_df_combined, _ = read_scenario_csvs("Results/Results_CSC/CSC_DAC_capacity.csv")
csc_credit_df_combined, _ = read_scenario_csvs("Results/Results_CSC/CSC_DAC_capacity.csv")


# ---------------------------------------------------------------------
# Load Dolphyn process-parameter files
# ---------------------------------------------------------------------

sf_process_dfs = read_process_csvs("LFSC_Synfuel_Resources.csv")
syn_ng_process_dfs = read_process_csvs("NGSC_Syn_NG_Resources.csv")
hsc_process_dfs = read_process_csvs("HSC_generation.csv")

bio_LF_process_dfs = read_process_csvs("BESC_Bio_Liquid_Fuels.csv")
bio_H2_process_dfs = read_process_csvs("BESC_Bio_H2.csv")
bio_Electricity_process_dfs = read_process_csvs("BESC_Bio_Electricity.csv")
bio_NG_process_dfs = read_process_csvs("BESC_Bio_Natural_Gas.csv")

csc_process_dfs = read_process_csvs("CSC_capture.csv")
csc_credit_process_dfs = read_process_csvs("CSC_capture.csv")


# ---------------------------------------------------------------------
# Process Dolphyn power-sector generation
# ---------------------------------------------------------------------

resource_abr = [
    r"natural(?!.*ccs)",
    r"naturalgas_ccccsavgcf",
    r"nuclear",
    r"conventional_hydroelectric|small_hydroelectric",
    r"solar|pv",
    r"wind",
    r"H2",
    r"Bio|Gasification|Pyrolysis|FT",
]

resource_name = [
    "NG",
    "NG CCS",
    "Nuclear",
    "Hydro",
    "Solar",
    "Wind",
    "H2G2P",
    "Bioenergy Credit",
]

df_combined["Resource_Category"] = None

for pattern, name in zip(resource_abr, resource_name):
    mask = df_combined["Resource"].astype(str).str.contains(
        pattern,
        case=False,
        regex=True,
        na=False,
    )
    df_combined.loc[mask, "Resource_Category"] = name

df_combined["AnnualGeneration"] = (
    pd.to_numeric(df_combined["AnnualGeneration"], errors="coerce")
    .fillna(0.0)
    * conversion_factor
)

aggregated_data = aggregate_by_scenario_category(
    df_combined[df_combined["Resource_Category"].notna()].copy(),
    "AnnualGeneration",
)


# ---------------------------------------------------------------------
# Process synthetic liquid fuels power consumption
# ---------------------------------------------------------------------

sf_df_combined["Resource_Category"] = "Synthetic FT"

sf_merged_combined = merge_scenario_process_data(
    result_df=sf_df_combined,
    process_dfs=sf_process_dfs,
    result_key="Resource",
    process_key="Syn_Fuel_Resource",
    process_cols=["mwh_p_tonne_co2"],
)

sf_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(sf_merged_combined["Annual_CO2_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(sf_merged_combined["mwh_p_tonne_co2"], errors="coerce").fillna(0.0)
    * conversion_factor
)

sf_aggregated_data = aggregate_by_scenario_category(
    sf_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process synthetic natural gas power consumption
# ---------------------------------------------------------------------

syn_ng_df_combined["Resource_Category"] = "Synthetic NG"

syn_ng_merged_combined = merge_scenario_process_data(
    result_df=syn_ng_df_combined,
    process_dfs=syn_ng_process_dfs,
    result_key="Resource",
    process_key="Syn_NG_Resource",
    process_cols=["mwh_p_tonne_co2"],
)

syn_ng_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(syn_ng_merged_combined["Annual_CO2_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(syn_ng_merged_combined["mwh_p_tonne_co2"], errors="coerce").fillna(0.0)
    * conversion_factor
)

syn_ng_aggregated_data = aggregate_by_scenario_category(
    syn_ng_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process H2 production power consumption
# ---------------------------------------------------------------------

hsc_df_combined["Resource_Category"] = "H2 Production"

hsc_merged_combined = merge_scenario_process_data(
    result_df=hsc_df_combined,
    process_dfs=hsc_process_dfs,
    result_key="Resource",
    process_key="H2_Resource",
    process_cols=["etaP2G"],
)

hsc_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(hsc_merged_combined["AnnualGeneration"], errors="coerce").fillna(0.0)
    * pd.to_numeric(hsc_merged_combined["etaP2G"], errors="coerce").fillna(0.0)
    * conversion_factor
)

hsc_aggregated_data = aggregate_by_scenario_category(
    hsc_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process DAC power consumption
# ---------------------------------------------------------------------

csc_df_combined["Resource_Category"] = "Sorbent DAC Input"

csc_merged_combined = merge_scenario_process_data(
    result_df=csc_df_combined,
    process_dfs=csc_process_dfs,
    result_key="Resource",
    process_key="CO2_Resource",
    process_cols=["etaPCO2_MWh_per_tonne"],
)

csc_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(csc_merged_combined["Annual_Capture"], errors="coerce").fillna(0.0)
    * pd.to_numeric(csc_merged_combined["etaPCO2_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

csc_aggregated_data = aggregate_by_scenario_category(
    csc_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process solvent DAC power credit
# ---------------------------------------------------------------------

csc_credit_df_combined["Resource_Category"] = "Solvent DAC Power Credit"

csc_credit_merged_combined = merge_scenario_process_data(
    result_df=csc_credit_df_combined,
    process_dfs=csc_credit_process_dfs,
    result_key="Resource",
    process_key="CO2_Resource",
    process_cols=["Power_Production_MWh_per_tonne"],
)

csc_credit_merged_combined["Annual_Power_Credit_EJ"] = (
    pd.to_numeric(csc_credit_merged_combined["Annual_Capture"], errors="coerce").fillna(0.0)
    * pd.to_numeric(csc_credit_merged_combined["Power_Production_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

csc_credit_aggregated_data = aggregate_by_scenario_category(
    csc_credit_merged_combined,
    "Annual_Power_Credit_EJ",
)


# ---------------------------------------------------------------------
# Process bio-H2 power consumption
# ---------------------------------------------------------------------

bio_H2_df_combined["Resource_Category"] = "Bio H2 Input"

bio_H2_merged_combined = merge_scenario_process_data(
    result_df=bio_H2_df_combined,
    process_dfs=bio_H2_process_dfs,
    result_key="Resource",
    process_key="Biorefinery",
    process_cols=["Power_consumption_MWh_per_tonne"],
)

bio_H2_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(bio_H2_merged_combined["Annual_Biomass_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(bio_H2_merged_combined["Power_consumption_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

bio_H2_aggregated_data = aggregate_by_scenario_category(
    bio_H2_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process bio-liquid-fuels power consumption
# ---------------------------------------------------------------------

bio_LF_df_combined["Resource_Category"] = "Bio LF Input"

bio_LF_merged_combined = merge_scenario_process_data(
    result_df=bio_LF_df_combined,
    process_dfs=bio_LF_process_dfs,
    result_key="Resource",
    process_key="Biorefinery",
    process_cols=["Power_consumption_MWh_per_tonne"],
)

bio_LF_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(bio_LF_merged_combined["Annual_Biomass_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(bio_LF_merged_combined["Power_consumption_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

bio_LF_aggregated_data = aggregate_by_scenario_category(
    bio_LF_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process bio-electricity power consumption
# ---------------------------------------------------------------------

bio_Electricity_df_combined["Resource_Category"] = "Bio Electricity Input"

bio_Electricity_merged_combined = merge_scenario_process_data(
    result_df=bio_Electricity_df_combined,
    process_dfs=bio_Electricity_process_dfs,
    result_key="Resource",
    process_key="Biorefinery",
    process_cols=["Power_consumption_MWh_per_tonne"],
)

bio_Electricity_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(bio_Electricity_merged_combined["Annual_Biomass_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(bio_Electricity_merged_combined["Power_consumption_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

bio_Electricity_aggregated_data = aggregate_by_scenario_category(
    bio_Electricity_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process bio-natural-gas power consumption
# ---------------------------------------------------------------------

bio_NG_df_combined["Resource_Category"] = "Bio NG Input"

bio_NG_merged_combined = merge_scenario_process_data(
    result_df=bio_NG_df_combined,
    process_dfs=bio_NG_process_dfs,
    result_key="Resource",
    process_key="Biorefinery",
    process_cols=["Power_consumption_MWh_per_tonne"],
)

bio_NG_merged_combined["Annual_Power_Consumption_EJ"] = (
    -pd.to_numeric(bio_NG_merged_combined["Annual_Biomass_Consumption"], errors="coerce").fillna(0.0)
    * pd.to_numeric(bio_NG_merged_combined["Power_consumption_MWh_per_tonne"], errors="coerce").fillna(0.0)
    * conversion_factor
)

bio_NG_aggregated_data = aggregate_by_scenario_category(
    bio_NG_merged_combined,
    "Annual_Power_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Compute Dolphyn electricity demand from Load_data.csv and time_weights.csv
# ---------------------------------------------------------------------

dolphyn_demand_ej = {}

for scen_short, scen_folder in dolphyn_scenario_paths.items():
    scenario_dir = os.path.join(dolphyn_base_dir, scen_folder)

    dolphyn_demand_ej[scen_short] = compute_dolphyn_power_demand_ej(
        scenario_dir
    )

demand_data = {
    scen: -dolphyn_demand_ej[scen]
    for scen in scenario_names
}

demand_df = pd.DataFrame.from_dict(
    demand_data,
    orient="index",
    columns=["Demand"],
)

print("Dolphyn weighted electricity demand by scenario (EJ):")
print(pd.Series(dolphyn_demand_ej).reindex(scenario_names))


# ---------------------------------------------------------------------
# Combine Dolphyn electricity balance categories
# ---------------------------------------------------------------------

combined_data = pd.concat(
    [
        aggregated_data,
        csc_credit_aggregated_data,
        hsc_aggregated_data,
        csc_aggregated_data,
        demand_df,
        sf_aggregated_data,
        syn_ng_aggregated_data,
        bio_H2_aggregated_data,
        bio_LF_aggregated_data,
        bio_Electricity_aggregated_data,
        bio_NG_aggregated_data,
    ],
    axis=1,
).fillna(0.0)

combine_mapping = {
    "Bioenergy Credit": "Bioenergy Input",
    "Bio H2 Input": "Bioenergy Input",
    "Bio LF Input": "Bioenergy Input",
    "Bio Electricity Input": "Bioenergy Input",
    "Bio NG Input": "Bioenergy Input",
    "Solvent DAC Power Credit": "NG CCS",
}

combined_data = combined_data.rename(columns=combine_mapping)

# group duplicate columns after renaming
combined_data = combined_data.T.groupby(level=0).sum().T

desired_order = [
    "Demand",
    "H2 Production",
    "Sorbent DAC Input",
    "Bioenergy Input",
    "Ethylene Input",
    "Ethanol Input",
    "Synthetic FT",
    "Synthetic NG",
    "Hydro",
    "Nuclear",
    "NG",
    "NG CCS",
    "Solar",
    "Wind",
]

combined_data = combined_data.reindex(scenario_names).fillna(0.0)

for col in desired_order:
    if col not in combined_data.columns:
        combined_data[col] = 0.0

combined_data = combined_data[desired_order]


# ---------------------------------------------------------------------
# Add MACRO electricity balance from annual_flows_balance_Power.csv
# ---------------------------------------------------------------------

macro_power_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_power_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Power.csv",
    )

    if not os.path.exists(macro_power_path):
        print(f"Warning: MACRO power balance file not found: {macro_power_path}")
        continue

    macro_power = pd.read_csv(macro_power_path)
    macro_power.columns = macro_power.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_power.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_power_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_power.columns.tolist()}"
        )

    macro_power["Scenario"] = scen_short
    macro_power["Annual_Flow"] = (
        pd.to_numeric(macro_power["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * conversion_factor
    )

    macro_power["Plot_Category"] = macro_power.apply(
        map_macro_power_category,
        axis=1,
    )

    macro_power = macro_power[macro_power["Plot_Category"].notna()].copy()

    macro_power_tables.append(macro_power)


if macro_power_tables:
    macro_power_combined = pd.concat(macro_power_tables, ignore_index=True)

    macro_combined_data = (
        macro_power_combined
        .groupby(["Scenario", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )
else:
    macro_combined_data = pd.DataFrame(index=scenario_names)

for col in desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

macro_combined_data = macro_combined_data[desired_order]

# Final plotting order: no transmission losses, storage losses, or H2 turbines
full_desired_order = desired_order.copy()

combined_data = combined_data[full_desired_order]
macro_combined_data = macro_combined_data[full_desired_order]


# ---------------------------------------------------------------------
# Plot settings
# ---------------------------------------------------------------------

category_colors = {
    "Hydro": "blue",
    "Nuclear": "red",
    "NG": "lightgrey",
    "NG CCS": "lightpink",
    "Solar": "gold",
    "Wind": "dodgerblue",
    "Sorbent DAC Input": "darkblue",
    "Bioenergy Input": "seagreen",
    "Ethylene Input": "#e8630a",
    "Ethanol Input": "#4caf72",
    "Synthetic NG": "violet",
    "Synthetic FT": "purple",
    "H2 Production": "lightgreen",
    "Demand": "bisque",
}

category_names = {
    "Demand": "Demand",
    "H2 Production": "Electrolyzer",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Bioenergy Input": "Biofuel Prod.",
    "Sorbent DAC Input": "Sorbent DAC",
    "Ethylene Input": "Ethylene Sector",
    "Ethanol Input": "Ethanol Sector",
    "Hydro": "Hydro",
    "Nuclear": "Nuclear",
    "NG": "NG",
    "NG CCS": "NG CCS",
    "Solar": "Solar",
    "Wind": "Wind",
}


# ---------------------------------------------------------------------
# Build paired plotting table
# ---------------------------------------------------------------------

plot_rows = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(combined_data.loc[scen, full_desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, full_desired_order])
    plot_index.append((scen, "MACRO"))

plot_df = pd.DataFrame(plot_rows)
plot_df.index = pd.MultiIndex.from_tuples(
    plot_index,
    names=["Scenario", "Model"],
)

y_tick_labels = [
    "D" if model == "Dolphyn" else "M"
    for _, model in plot_df.index
]


# ---------------------------------------------------------------------
# Plot Dolphyn and MACRO side by side with spacing between scenarios
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(4.9, 3.4))

pair_gap = 0.45
bar_height = 0.72

bar_positions = []

for i in range(len(scenario_names)):
    base = i * (2 + pair_gap)
    bar_positions.extend([base, base + 1])

plot_df.plot(
    kind="barh",
    stacked=True,
    width=bar_height,
    ax=ax,
    color=[category_colors[col] for col in full_desired_order],
)

# Move bars from default positions 0, 1, 2, ... to custom positions with gaps
for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Electricity Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-50, 50)
ax.set_xticks([-40, -20, 0, 20, 40])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Put HB-HS / HB-LS / LB-HS / LB-LS labels to the left of each D/M pair
for i, scen in enumerate(scenario_names):
    y_mid = i * (2 + pair_gap) + 0.5
    ax.text(
        -0.16,
        y_mid,
        scen,
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="center",
        fontsize=14,
    )

# Keep HB-HS at the top
ax.set_ylim(max(bar_positions) + 0.8, -0.8)

# Custom legend
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in full_desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.28),
    ncol=2,
    fontsize=12,
    frameon=False,
)


plt.subplots_adjust(left=0.24, right=0.98, top=0.88, bottom=0.36)

plt.show()