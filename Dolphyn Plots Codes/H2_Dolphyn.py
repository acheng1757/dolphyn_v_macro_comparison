import os
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

scenario_names = ["HB-HS", "HB-LS", "LB-HS", "LB-LS"]

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ

dolphyn_scenario_paths = {
    "HB-HS": "NineZones_High_Biomass_High_CO2",
    "HB-LS": "NineZones_High_Biomass_Low_CO2",
    "LB-HS": "NineZones_Low_Biomass_High_CO2",
    "LB-LS": "NineZones_Low_Biomass_Low_CO2",
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


def read_time_weights(time_weights_path):
    """
    Read Dolphyn time_weights.csv and return a 1-D Series of hourly weights.
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


def compute_dolphyn_h2_demand_ej(scenario_dir):
    """
    Compute total weighted H2 demand for one Dolphyn scenario.

    Assumes:
      - HSC_load_data.csv is in TDR_Results/
      - time_weights.csv is in Results/
      - H2 load columns are named Load_H2_MW_z1, Load_H2_MW_z2, ...
      - hourly MW * time weight gives MWh
    """
    h2_load_path = os.path.join(
        scenario_dir,
        "TDR_Results",
        "HSC_load_data.csv",
    )

    time_weights_path = os.path.join(
        scenario_dir,
        "Results",
        "time_weights.csv",
    )

    if not os.path.exists(h2_load_path):
        raise FileNotFoundError(f"HSC_load_data.csv not found: {h2_load_path}")

    if not os.path.exists(time_weights_path):
        raise FileNotFoundError(f"time_weights.csv not found: {time_weights_path}")

    h2_load_df = pd.read_csv(h2_load_path)
    h2_load_df.columns = h2_load_df.columns.str.strip()

    h2_load_cols = [
        c for c in h2_load_df.columns
        if c.lower().startswith("load_h2_mw")
    ]

    if not h2_load_cols:
        raise ValueError(
            f"No Load_H2_MW* columns found in {h2_load_path}. "
            f"Available columns are: {h2_load_df.columns.tolist()}"
        )

    hourly_global_h2_load_mw = (
        h2_load_df[h2_load_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .sum(axis=1)
    )

    time_weights = read_time_weights(time_weights_path)

    if len(time_weights) != len(hourly_global_h2_load_mw):
        raise ValueError(
            f"Length mismatch for {scenario_dir}: "
            f"{len(hourly_global_h2_load_mw)} H2 load rows but "
            f"{len(time_weights)} time weights."
        )

    total_h2_demand_mwh = (hourly_global_h2_load_mw * time_weights).sum()
    total_h2_demand_ej = total_h2_demand_mwh * MWH_TO_EJ

    return total_h2_demand_ej


def categorize_dolphyn_h2_resource(resource):
    """
    Categorize Dolphyn HSC_generation_storage_capacity.csv resources.
    """
    resource_str = str(resource)

    if "Electrolyzer" in resource_str:
        return "Electrolyzer"

    if "wCCS" in resource_str:
        return "NG CCS H2"

    if "Bio" in resource_str:
        return "BECCS H2"

    return None


# ---------------------------------------------------------------------
# Load Dolphyn H2-related result files
# ---------------------------------------------------------------------

hsc_df_combined, _ = read_scenario_csvs(
    "Results/Results_HSC/HSC_generation_storage_capacity.csv"
)

sf_df_combined, _ = read_scenario_csvs(
    "Results/Results_LF/Synfuel_capacity.csv"
)

syn_ng_df_combined, _ = read_scenario_csvs(
    "Results/Results_NG/Syn_ng_capacity.csv"
)


# ---------------------------------------------------------------------
# Load Dolphyn process-parameter files
# ---------------------------------------------------------------------

sf_process_dfs = read_process_csvs("LFSC_Synfuel_Resources.csv")
syn_ng_process_dfs = read_process_csvs("NGSC_Syn_NG_Resources.csv")


# ---------------------------------------------------------------------
# Process Dolphyn H2 production
# ---------------------------------------------------------------------

hsc_df_combined["Resource_Category"] = hsc_df_combined["Resource"].apply(
    categorize_dolphyn_h2_resource
)

hsc_filtered = hsc_df_combined[
    hsc_df_combined["Resource_Category"].notna()
].copy()

hsc_filtered["AnnualGeneration"] = (
    pd.to_numeric(hsc_filtered["AnnualGeneration"], errors="coerce")
    .fillna(0.0)
    * conversion_factor
)

hsc_aggregated_data = aggregate_by_scenario_category(
    hsc_filtered,
    "AnnualGeneration",
)


# ---------------------------------------------------------------------
# Process Dolphyn synthetic liquid fuels H2 consumption
# ---------------------------------------------------------------------

sf_df_combined["Resource_Category"] = "Synthetic FT"

sf_merged_combined = merge_scenario_process_data(
    result_df=sf_df_combined,
    process_dfs=sf_process_dfs,
    result_key="Resource",
    process_key="Syn_Fuel_Resource",
    process_cols=["mwh_h2_p_tonne_co2"],
)

sf_merged_combined["Annual_H2_Consumption_EJ"] = (
    -pd.to_numeric(
        sf_merged_combined["Annual_CO2_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        sf_merged_combined["mwh_h2_p_tonne_co2"],
        errors="coerce",
    ).fillna(0.0)
    * conversion_factor
)

sf_aggregated_data = aggregate_by_scenario_category(
    sf_merged_combined,
    "Annual_H2_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Process Dolphyn synthetic natural gas H2 consumption
# ---------------------------------------------------------------------

syn_ng_df_combined["Resource_Category"] = "Synthetic NG"

syn_ng_merged_combined = merge_scenario_process_data(
    result_df=syn_ng_df_combined,
    process_dfs=syn_ng_process_dfs,
    result_key="Resource",
    process_key="Syn_NG_Resource",
    process_cols=["mwh_h2_p_tonne_co2"],
)

syn_ng_merged_combined["Annual_H2_Consumption_EJ"] = (
    -pd.to_numeric(
        syn_ng_merged_combined["Annual_CO2_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        syn_ng_merged_combined["mwh_h2_p_tonne_co2"],
        errors="coerce",
    ).fillna(0.0)
    * conversion_factor
)

syn_ng_aggregated_data = aggregate_by_scenario_category(
    syn_ng_merged_combined,
    "Annual_H2_Consumption_EJ",
)


# ---------------------------------------------------------------------
# Dolphyn H2 demand from TDR_Results/HSC_load_data.csv and Results/time_weights.csv
# ---------------------------------------------------------------------

dolphyn_h2_demand_ej = {}

for scen_short, scen_folder in dolphyn_scenario_paths.items():
    scenario_dir = os.path.join(dolphyn_base_dir, scen_folder)

    dolphyn_h2_demand_ej[scen_short] = compute_dolphyn_h2_demand_ej(
        scenario_dir
    )

demand_data = {
    scen: -dolphyn_h2_demand_ej[scen]
    for scen in scenario_names
}

demand_df = pd.DataFrame.from_dict(
    demand_data,
    orient="index",
    columns=["Demand"],
)

print("Dolphyn weighted H2 demand by scenario (EJ):")
print(pd.Series(dolphyn_h2_demand_ej).reindex(scenario_names))


# ---------------------------------------------------------------------
# Combine Dolphyn H2 balance
# ---------------------------------------------------------------------

combined_data = pd.concat(
    [
        hsc_aggregated_data,
        demand_df,
        sf_aggregated_data,
        syn_ng_aggregated_data,
    ],
    axis=1,
).fillna(0.0)

combined_data = combined_data.T.groupby(level=0).sum().T

desired_order = [
    "Demand",
    "Synthetic FT",
    "Synthetic NG",
    "Electrolyzer",
    "NG CCS H2",
    "BECCS H2",
]

combined_data = combined_data.reindex(scenario_names).fillna(0.0)

for col in desired_order:
    if col not in combined_data.columns:
        combined_data[col] = 0.0

combined_data = combined_data[desired_order]


# ---------------------------------------------------------------------
# Print balance table for checking
# ---------------------------------------------------------------------

print("\nDolphyn H2 balance by scenario (EJ):")
print(combined_data)


# ---------------------------------------------------------------------
# Plot settings
# ---------------------------------------------------------------------

category_colors = {
    "Electrolyzer": "lightgreen",
    "NG CCS H2": "deepskyblue",
    "BECCS H2": "seagreen",
    "Synthetic FT": "purple",
    "Synthetic NG": "violet",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Demand": "Demand",
}


# ---------------------------------------------------------------------
# Plot Dolphyn-only H2 balance
# ---------------------------------------------------------------------

plot_df = combined_data[desired_order].copy()

fig, ax = plt.subplots(figsize=(5.0, 3.0))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)

ax.set_ylabel("")
ax.set_title("H2 Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-18, 18)
ax.set_xticks([-16, -8, 0, 8, 16])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

# Custom legend
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.28),
    ncol=2,
    fontsize=12,
    frameon=False,
)

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.34)

plt.show()