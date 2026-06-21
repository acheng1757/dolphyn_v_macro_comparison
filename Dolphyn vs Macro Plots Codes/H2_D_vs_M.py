import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir,
    dolphyn_results_folder, scenario_names,
)

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ
mwh_h2_p_t_h2 = 39.39
mwh_h2_p_tonne_h2 = 39.39

dolphyn_scenario_paths = {
    "1": "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn/all_demand_test/",
}

macro_scenario_paths = {
    "1": f"6_15_168_restart_all_demand/results_001/results",
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
        path = os.path.join(scen_folder, relative_path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found for {scen}: {path}")

        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        df["Scenario"] = scen
        scenario_dfs[scen] = df

    combined = pd.concat(
        [scenario_dfs[scen] for scen in dolphyn_scenario_paths],
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
        path = os.path.join(scen_folder, relative_path)

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

    for scen in dolphyn_scenario_paths:
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
        dolphyn_results_folder,
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
        if c.lower().startswith("load_h2_tonne")
    ]

    if not h2_load_cols:
        raise ValueError(
            f"No load_h2_tonne* columns found in {h2_load_path}. "
            f"Available columns are: {h2_load_df.columns.tolist()}"
        )

    hourly_global_h2_load_t = (
        h2_load_df[h2_load_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .sum(axis=1)
    )

    time_weights = read_time_weights(time_weights_path)

    if len(time_weights) != len(hourly_global_h2_load_t):
        raise ValueError(
            f"Length mismatch for {scenario_dir}: "
            f"{len(hourly_global_h2_load_t)} H2 load rows but "
            f"{len(time_weights)} time weights."
        )

    total_h2_demand_t = (hourly_global_h2_load_t * time_weights).sum()
    total_h2_demand_mwh = total_h2_demand_t * mwh_h2_p_tonne_h2
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


def map_macro_h2_category(row):
    """
    Map MACRO annual_flows_balance_H2.csv rows to the same H2-balance
    plotting categories used for Dolphyn.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Demand rows
    if sector == "Demand":
        return "Demand"

    # H2 production technologies
    if sector == "Hydrogen":
        category_lower = category.lower()

        if "electrolyzer" in category_lower:
            return "Electrolyzer"

        if category in ["NG CCS H2", "NG CCS"]:
            return "NG CCS H2"

        if "ccs" in category_lower and (
            "ng" in category_lower or "natural" in category_lower
        ):
            return "NG CCS H2"

        if "bio" in category_lower or "beccs" in category_lower:
            return "BECCS H2"

        # Exclude H2 storage / compressor / other small internal flows unless desired
        if (
            "stor" in category_lower
            or "storage" in category_lower
            or "comp" in category_lower
        ):
            return None

        return None

    # Synthetic-fuel H2 consumption
    if sector == "Synthetic fuels":
        if category == "S-NG":
            return "Synthetic NG"

        if category in ["S-J", "S-J-CC99", "S-J-99"]:
            return "Synthetic FT"

        category_lower = category.lower()

        if "ng" in category_lower:
            return "Synthetic NG"

        if (
            "s-j" in category_lower
            or "jet" in category_lower
            or "ft" in category_lower
        ):
            return "Synthetic FT"

        return None

    # Bioenergy H2 production if represented outside Hydrogen sector
    if sector == "Bioenergy":
        category_lower = category.lower()

        if (
            "h2" in category_lower
            or "hydrogen" in category_lower
            or "bio" in category_lower
        ):
            return "BECCS H2"

        return None

    if sector == "Ethylene":
        return "Ethylene Sector"

    return None

def compute_ethylene_h2_production_ej(scenario_dir):
    """
    Read H2 production from ethylene process from HSC_h2_balance.csv.
    Sums 'Production from Ethylene Process' across all zones from the AnnualSum row.
    """
    path = os.path.join(scenario_dir, dolphyn_results_folder, "Results_HSC", "HSC_h2_balance.csv")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"HSC_h2_balance.csv not found: {path}")
    
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    
    # Get the AnnualSum row
    annual_row = df[df["Unnamed: 0"] == "AnnualSum"]
    
    # Sum across all zone columns for this term
    eth_cols = [c for c in df.columns if c.startswith("Production from Ethylene Process")]
    
    total_tonnes = (
        annual_row[eth_cols]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0.0)
        .values.sum()
    )
    
    return total_tonnes * MWH_TO_EJ * mwh_h2_p_tonne_h2

H2_ASSETS = ["TSC+H2in:CH4", "TSC+H2in","MS+MTO+CC90","Bio-eth+CC88:H2"]

# Maps CSV asset names → Ethylene_Resource keys in the process parameter files
RESOURCE_MAPPING = {
    "TSC+H2in:CH4": "F-H2in-CH4out",
    "TSC+H2in":     "F-H2in",
    "MS+MTO+CC90":     "S-CC90-H2in",
    "Bio-eth+CC88:H2":     "B-H2in",
}

def load_ethylene_retrofit_balance(
    csv_path: str,
    assets: list[str] = H2_ASSETS,
    resource_mapping: dict[str, str] = RESOURCE_MAPPING,
) -> pd.DataFrame:
    """
    Parse Ethylene_Retrofit_Balance.csv into a long-form DataFrame suitable
    for merging into the ethylene aggregation pipeline.

    The raw CSV has one column per (asset, zone) pair.  Base columns are named
    after the asset; repeated zones get pandas' automatic de-duplication suffix
    (.1, .2, …).  Row 0 carries the zone number; row 1 is the annual sum;
    rows 2+ are time-steps t1…tN.

    resource_mapping translates CSV asset names to the Ethylene_Resource keys
    used in the process parameter files (e.g. "TSC+H2in:CH4" → "F-H2in-CH4out").

    Returns columns:
        Resource                  – mapped process key (e.g. "F-H2in-CH4out")
        Zone                      – zone number (int)
        AnnualSum                 – annual sum value for that asset/zone
        Annual_ethane_Consumption – negated AnnualSum (sign convention for H2 calc)
        Time                      – time-step label ("AnnualSum", "t1", …)
        Value                     – raw balance value
    """
    raw = pd.read_csv(csv_path, header=0)
    time_col = raw.columns[0]

    records = []

    for base_asset in assets:
        asset_cols = [
            c for c in raw.columns
            if c == base_asset or c.startswith(base_asset + ".")
        ]

        for col in asset_cols:
            zone = int(raw.loc[raw[time_col] == "Zone", col].values[0])

            for _, row in raw[raw[time_col] != "Zone"].iterrows():
                records.append(
                    {
                        "Resource": base_asset,   # raw name; mapped below
                        "Zone":     zone,
                        "Time":     row[time_col],
                        "Value":    pd.to_numeric(row[col], errors="coerce"),
                    }
                )

    df = pd.DataFrame(records)

    # Pivot AnnualSum out as its own column
    annual = (
        df[df["Time"] == "AnnualSum"]
        .rename(columns={"Value": "AnnualSum"})
        [["Resource", "Zone", "AnnualSum"]]
    )
    df = df.merge(annual, on=["Resource", "Zone"], how="left")

    # Apply name mapping BEFORE the downstream merge so process keys align
    if resource_mapping:
        df["Resource"] = df["Resource"].replace(resource_mapping)

    # Sign convention: consumption is negative in the balance → flip for merge
    df["Annual_ethane_Consumption"] = -df["AnnualSum"] # this is an incorrect name

    return df

def merge_scenario_process_data_by_zone(
    result_df,
    process_dfs,
    result_key,
    process_key,
    result_zone_key,
    process_zone_key,
    process_cols,
):
    """
    Like merge_scenario_process_data but joins on both resource name and zone,
    needed for retrofit assets where parameters vary by zone.
    """
    merged_tables = []

    for scen in dolphyn_scenario_paths:
        result_scen = result_df[result_df["Scenario"] == scen].copy()
        process_scen = process_dfs[scen][
            [process_key, process_zone_key] + process_cols
        ].copy()

        merged = pd.merge(
            result_scen,
            process_scen,
            left_on=[result_key, result_zone_key],
            right_on=[process_key, process_zone_key],
            how="left",
        )

        merged_tables.append(merged)

    return pd.concat(merged_tables, ignore_index=True)

# ---------------------------------------------------------------------
# Load Dolphyn H2-related result files
# ---------------------------------------------------------------------

hsc_df_combined, _ = read_scenario_csvs(
    f'{dolphyn_results_folder}/Results_HSC/HSC_generation_storage_capacity.csv'
)

sf_df_combined, _ = read_scenario_csvs(
    f'{dolphyn_results_folder}/Results_LF/Synfuel_capacity.csv'
)

syn_ng_df_combined, _ = read_scenario_csvs(
    f'{dolphyn_results_folder}/Results_NG/Syn_ng_capacity.csv'
)

# ADD RETROFIT AND STUFF LATER
ethylene_df_combined, _ = read_scenario_csvs(
    f'{dolphyn_results_folder}/Results_Ethylene/Ethylene_capacity.csv'
)
_eth_df = pd.read_csv(os.path.join(dolphyn_scenario_paths[scenario_names[0]], "Ethylene_Resources.csv"))
_eth_df.columns = _eth_df.columns.str.strip()
ethylene_process_dfs = {scenario_names[0]: _eth_df}

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
    * mwh_h2_p_tonne_h2
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
    process_cols=["tonnes_h2_p_tonne_co2"],
)

sf_merged_combined["Annual_H2_Consumption_EJ"] = (
    -pd.to_numeric(
        sf_merged_combined["Annual_CO2_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        sf_merged_combined["tonnes_h2_p_tonne_co2"],
        errors="coerce",
    ).fillna(0.0)
    * mwh_h2_p_tonne_h2
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
    process_cols=["tonnes_h2_p_tonne_co2"],
)

syn_ng_merged_combined["Annual_H2_Consumption_EJ"] = (
    -pd.to_numeric(
        syn_ng_merged_combined["Annual_CO2_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        syn_ng_merged_combined["tonnes_h2_p_tonne_co2"],
        errors="coerce",
    ).fillna(0.0)
    * mwh_h2_p_tonne_h2
    * conversion_factor
)

syn_ng_aggregated_data = aggregate_by_scenario_category(
    syn_ng_merged_combined,
    "Annual_H2_Consumption_EJ",
)

# ---------------------------------------------------------------------
# Process Dolphyn H2 production from Ethylene
# ---------------------------------------------------------------------
eth_h2_production_ej = {}
for scen_short, scen_folder in dolphyn_scenario_paths.items():
    scenario_dir = os.path.join(dolphyn_base_dir, scen_folder)
    eth_h2_production_ej[scen_short] = compute_ethylene_h2_production_ej(scenario_dir)
    print('ethylene_production', eth_h2_production_ej[scen_short])

eth_production_df = pd.DataFrame.from_dict(
    eth_h2_production_ej,
    orient="index",
    columns=["Ethylene Sector"],
)

# ---------------------------------------------------------------------
# Process Dolphyn Ethylene H2 consumption from new build assets
# ---------------------------------------------------------------------

ethylene_df_combined["Resource_Category"] = "Ethylene Sector"

ethylene_merged_combined = merge_scenario_process_data(
    result_df=ethylene_df_combined,
    process_dfs=ethylene_process_dfs,
    result_key="Resource",
    process_key="Ethylene_Resource",
    process_cols=["tonnes_h2_p_tonne_ethylene","tonne_ethane_p_tonne_ethylene"],
)

ethylene_merged_combined["Annual_H2_Consumption_EJ"] = (
    -pd.to_numeric(
        ethylene_merged_combined["Annual_ethane_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        ethylene_merged_combined["tonnes_h2_p_tonne_ethylene"],
        errors="coerce",
    ).fillna(0.0)
    #/ pd.to_numeric(
    #    ethylene_merged_combined["tonne_ethane_p_tonne_ethylene"],
    #    errors="coerce",
    #).fillna(0.0)
    * mwh_h2_p_tonne_h2
    * conversion_factor
)

print('ethylene_merged_combined')
print(ethylene_merged_combined)

ethylene_aggregated_data = aggregate_by_scenario_category(
    ethylene_merged_combined,
    "Annual_H2_Consumption_EJ",
)

# ---------------------------------------------------------------------
# Process Dolphyn Ethylene H2 consumption from retrofit assets
# ---------------------------------------------------------------------

retrofit_df = load_ethylene_retrofit_balance(
    csv_path=os.path.join(dolphyn_scenario_paths[scenario_names[0]], dolphyn_results_folder, "Results_Ethylene", "Ethylene_Retrofit_Balance.csv"),
    assets=H2_ASSETS,
    resource_mapping=RESOURCE_MAPPING,
)
retrofit_df = retrofit_df[retrofit_df["Time"] == "AnnualSum"].copy()
retrofit_df["Scenario"] = scenario_names[0]
retrofit_df["Resource_Category"] = "Ethylene Sector"

# Merge on BOTH Resource and Zone so we pull the right zone-specific parameters
ethylene_retrofit_merged_combined = merge_scenario_process_data_by_zone(
    result_df=retrofit_df,
    process_dfs=ethylene_process_dfs,
    result_key="Resource",
    process_key="Ethylene_Resource",
    result_zone_key="Zone",
    process_zone_key="Zone",
    process_cols=["tonnes_h2in_p_tonne_ethylene", "tonne_ethane_p_tonne_ethylene"],
)

# For F-H2in / F-H2in-CH4out the H2 input per tonne ethylene is in
# tonnes_h2in_p_tonne_ethylene, so use that directly instead of the
# ethane-ratio calculation used for new-build assets.
ethylene_retrofit_merged_combined["Annual_H2_Consumption_EJ"] = (
    pd.to_numeric(
        ethylene_retrofit_merged_combined["Annual_ethane_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        ethylene_retrofit_merged_combined["tonnes_h2in_p_tonne_ethylene"],
        errors="coerce",
    ).fillna(0.0)
    #/ pd.to_numeric(
    #    ethylene_retrofit_merged_combined["tonne_ethane_p_tonne_ethylene"],
    #    errors="coerce",
    #).fillna(0.0)
    * mwh_h2_p_tonne_h2
    * conversion_factor
)

print("ethylene_retrofit_merged_combined")
print(ethylene_retrofit_merged_combined)

ethylene_retrofit_aggregated_data = aggregate_by_scenario_category(
    ethylene_retrofit_merged_combined,
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

# Demand is negative in the H2 balance plot
demand_data = {
    scen: -dolphyn_h2_demand_ej[scen]
    for scen in dolphyn_scenario_paths
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
        eth_production_df,
        ethylene_aggregated_data,
        ethylene_retrofit_aggregated_data,
    ],
    axis=1,
).fillna(0.0)

# group duplicate columns if any
combined_data = combined_data.T.groupby(level=0).sum().T

desired_order = [
    "Ethylene Sector",
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
# Read MACRO H2 balance from annual_flows_balance_H2.csv
# ---------------------------------------------------------------------

macro_h2_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_h2_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_H2.csv",
    )

    if not os.path.exists(macro_h2_path):
        print(f"Warning: MACRO H2 balance file not found: {macro_h2_path}")
        continue

    macro_h2 = pd.read_csv(macro_h2_path)
    macro_h2.columns = macro_h2.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_h2.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_h2_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_h2.columns.tolist()}"
        )

    macro_h2["Scenario"] = scen_short
    macro_h2["Annual_Flow"] = (
        pd.to_numeric(macro_h2["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * conversion_factor
    )

    macro_h2["Plot_Category"] = macro_h2.apply(
        map_macro_h2_category,
        axis=1,
    )

    macro_h2 = macro_h2[macro_h2["Plot_Category"].notna()].copy()

    macro_h2_tables.append(macro_h2)


if macro_h2_tables:
    macro_h2_combined = pd.concat(macro_h2_tables, ignore_index=True)

    macro_combined_data = (
        macro_h2_combined
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


# ---------------------------------------------------------------------
# Optional: print balance tables for checking
# ---------------------------------------------------------------------

print("\nDolphyn H2 balance by scenario (EJ):")
print(combined_data)

print("\nMACRO H2 balance by scenario (EJ):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Plot settings
# ---------------------------------------------------------------------

category_colors = {
    "Electrolyzer": "lightgreen",
    "NG CCS H2": "deepskyblue",
    "BECCS H2": "seagreen",
    "Synthetic FT": "purple",
    "Synthetic NG": "violet",
    "Ethylene Sector": "#e8630a",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Ethylene Sector": "Ethylene Sector",
    "Demand": "Demand",
}

full_desired_order = desired_order.copy()


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
# Print net H2 balance (production + and consumption -) before plotting
# ---------------------------------------------------------------------

print("\nH2 Net Balance Summary (EJ):")
print(f"{'Scenario':<20} {'Model':<10} {'Production (+)':<18} {'Consumption (-)':<18} {'Net Balance':<12}")
print("-" * 80)
for (scen, model), row in plot_df.iterrows():
    production = row[row > 0].sum()
    consumption = row[row < 0].sum()
    net = production + consumption
    print(f"{scen:<20} {model:<10} {production:<18.4f} {consumption:<18.4f} {net:<12.4f}")

# ---------------------------------------------------------------------
# Plot Dolphyn and MACRO H2 balance side by side
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.0, 3.4))

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
ax.set_title("H2 Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-18, 18)
ax.set_xticks([-16, -8, 0, 8, 16])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Scenario labels to the left of each D/M pair
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

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------
y_plotly_labels = [
    f"{scen} ({'D' if model == 'Dolphyn' else 'M'})"
    for scen, model in plot_df.index
]

fig_plotly = go.Figure()

for col in full_desired_order:
    display_name = category_names.get(col, col)
    color = category_colors.get(col, '#333333')
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=y_plotly_labels,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=color,
        hovertemplate='%{fullData.name}: %{x:.4f} EJ<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='H2 Balance (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'h2_d_vs_m_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')