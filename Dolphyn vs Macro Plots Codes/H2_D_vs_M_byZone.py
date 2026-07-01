#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir, dolphyn_results_folder,
)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ
mwh_h2_p_tonne_h2 = 39.39

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------
# Fully manual/self-contained: dolphyn_scenario_paths and
# macro_scenario_paths are the source of truth for which scenarios this
# script compares (same values as H2_D_vs_M.py). scenario_names is
# derived from them directly rather than imported from Step_1, so this
# script doesn't silently break or go stale whenever Step_1's shared
# scenario config changes.

dolphyn_scenario_paths = {
    "1": "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn/ethylene_only_test/",
    "2": "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn/ethylene_only_test/",
    "3": "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn/ethylene_only_test/",
}

macro_scenario_paths = {
    "1": f"7_1_DOLPHYN_B2/results_001/results",
    "2": f"7_1_DOLPHYN_B2/results_002/results",
    "3": f"7_1_DOLPHYN_B2/results_003/results",
}

scenario_names = list(dolphyn_scenario_paths.keys())

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def _zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


def _macro_extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name (same logic as
    H2_Macro_byZone.py's extract_zone).

    Production/consumption edges put the zone first:
        CA_Electrolyzer_h2_edge
        Existing_CEN_F-NGin-H2out_h2_production_edge
    Demand-sector edges put the zone last:
        Hydrogen_MW_NE
    """
    tokens = str(edge_name).split("_")
    candidates = tokens[:1]
    if tokens[:1] == ["Existing"] and len(tokens) > 1:
        candidates.append(tokens[1])
    if tokens:
        candidates.append(tokens[-1])

    for candidate in candidates:
        if candidate in zone_list:
            return candidate

    return None


def map_macro_h2_category(row):
    """
    Map MACRO annual_flows_balance_H2.csv rows to H2-balance plotting
    categories (same as H2_Macro.py / H2_Macro_byZone.py).
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    if sector == "Demand":
        return "Demand"

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

        if (
            "stor" in category_lower
            or "storage" in category_lower
            or "comp" in category_lower
        ):
            return None

        return None

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
        try:
            flow = float(row.get("Annual_Flow", 0.0))
        except (TypeError, ValueError):
            flow = 0.0
        return "Ethylene Sector Production" if flow >= 0 else "Ethylene Sector Consumption"

    if sector == "Ethanol Upgrading":
        return "Ethanol Upgrading"

    return None


# ---------------------------------------------------------------------
# Desired order, colors, and labels — merged Dolphyn + MACRO category
# set (same as the updated H2_D_vs_M.py), minus Non-Served Demand,
# which has no per-zone breakdown on the MACRO side.
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Steam Cracker Ethylene Prod",
    "Steam Cracker Ethylene Consumption",
    "Ethylene Sector Production",
    "Ethylene Sector Consumption",
    "Ethanol Upgrading",
    "Synthetic FT",
    "Synthetic NG",
    "Electrolyzer",
    "NG CCS H2",
    "BECCS H2",
]

category_colors = {
    "Electrolyzer": "lightgreen",
    "NG CCS H2": "deepskyblue",
    "BECCS H2": "seagreen",
    "Synthetic FT": "purple",
    "Synthetic NG": "#e8905a",
    "Ethylene Sector Production": "#e8630a",
    "Ethylene Sector Consumption": "#7a2e0e",
    "Steam Cracker Ethylene Prod": "red",
    "Steam Cracker Ethylene Consumption": "orange",
    "Ethanol Upgrading": "#d4a017",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Ethylene Sector Production": "Ethylene Sector (Production)",
    "Ethylene Sector Consumption": "Ethylene Sector (Consumption)",
    "Steam Cracker Ethylene Prod": "Steam Cracker Ethylene Prod",
    "Steam Cracker Ethylene Consumption": "Steam Cracker Ethylene Consumption",
    "Ethanol Upgrading": "Ethanol Upgrading",
    "Demand": "Demand",
}


# ---------------------------------------------------------------------
# Dolphyn-side helper functions (unchanged from H2_Dolphyn_byZone.py —
# these already carry a Zone column through every merge)
# ---------------------------------------------------------------------

def read_scenario_csvs(relative_path):
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
        [scenario_dfs[scen] for scen in scenario_names],
        ignore_index=True,
    )

    return combined, scenario_dfs


def read_process_csvs(relative_path):
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


def categorize_dolphyn_h2_resource(resource):
    resource_str = str(resource)

    if "Electrolyzer" in resource_str:
        return "Electrolyzer"

    if "wCCS" in resource_str:
        return "NG CCS H2"

    if "Bio" in resource_str:
        return "BECCS H2"

    return None


H2_ASSETS = ["TSC+H2in:CH4", "TSC+H2in", "MS+MTO+CC90", "Bio-eth+CC88:H2"]

RESOURCE_MAPPING = {
    "TSC+H2in:CH4": "F-H2in-CH4out",
    "TSC+H2in":     "F-H2in",
    "MS+MTO+CC90":  "S-CC90-H2in",
    "Bio-eth+CC88:H2": "B-H2in",
}


def load_ethylene_retrofit_balance(
    csv_path: str,
    assets: list = H2_ASSETS,
    resource_mapping: dict = RESOURCE_MAPPING,
) -> pd.DataFrame:
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
                        "Resource": base_asset,
                        "Zone":     zone,
                        "Time":     row[time_col],
                        "Value":    pd.to_numeric(row[col], errors="coerce"),
                    }
                )

    df = pd.DataFrame(records)

    annual = (
        df[df["Time"] == "AnnualSum"]
        .rename(columns={"Value": "AnnualSum"})
        [["Resource", "Zone", "AnnualSum"]]
    )
    df = df.merge(annual, on=["Resource", "Zone"], how="left")

    if resource_mapping:
        df["Resource"] = df["Resource"].replace(resource_mapping)

    df["Annual_ethane_Consumption"] = -df["AnnualSum"]

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
    merged_tables = []

    for scen in scenario_names:
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


def aggregate_by_scenario_zone_category(df, value_col):
    """
    Aggregate a dataframe by Scenario, Zone, and Resource_Category.
    Returns {scenario: DataFrame indexed by zone_list, columns=Resource_Category}.
    """
    working = df.copy()
    working["ZoneName"] = pd.to_numeric(working["Zone"], errors="coerce").apply(
        lambda z: _zone_name(z) if pd.notna(z) else None
    )
    working = working[working["ZoneName"].notna()]

    tables = {}
    for scen in scenario_names:
        scen_df = working[working["Scenario"] == scen]
        table = (
            scen_df.groupby(["ZoneName", "Resource_Category"])[value_col]
            .sum()
            .unstack()
            .reindex(zone_list)
            .fillna(0.0)
        )
        tables[scen] = table

    return tables


def combine_zone_tables(*tables_by_scenario):
    """
    Combine several {scenario: zone-indexed DataFrame/Series} dicts into one
    DataFrame per scenario, merging duplicate column names by summation.
    """
    combined = {}
    for scen in scenario_names:
        parts = []
        for tables in tables_by_scenario:
            if scen not in tables:
                continue
            obj = tables[scen]
            if isinstance(obj, pd.Series):
                obj = obj.to_frame(name=obj.name)
            parts.append(obj)

        if not parts:
            combined[scen] = pd.DataFrame(index=zone_list)
            continue

        merged = pd.concat(parts, axis=1).fillna(0.0)
        merged = merged.T.groupby(level=0).sum().T
        combined[scen] = merged.reindex(zone_list).fillna(0.0)

    return combined


def compute_dolphyn_h2_demand_ej_by_zone(scenario_dir):
    h2_load_path = os.path.join(scenario_dir, "TDR_Results", "HSC_load_data.csv")
    time_weights_path = os.path.join(scenario_dir, dolphyn_results_folder, "time_weights.csv")

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

    time_weights = read_time_weights(time_weights_path)

    demand_by_zone = {}
    for col in h2_load_cols:
        match = re.search(r"z(\d+)$", col, re.IGNORECASE)
        if not match:
            continue
        zone_name = _zone_name(int(match.group(1)))

        hourly_load_t = pd.to_numeric(h2_load_df[col], errors="coerce").fillna(0.0)

        if len(time_weights) != len(hourly_load_t):
            raise ValueError(
                f"Length mismatch for {scenario_dir}, column {col}: "
                f"{len(hourly_load_t)} H2 load rows but {len(time_weights)} time weights."
            )

        total_t = (hourly_load_t * time_weights).sum()
        demand_by_zone[zone_name] = demand_by_zone.get(zone_name, 0.0) + total_t * mwh_h2_p_tonne_h2 * MWH_TO_EJ

    return pd.Series(demand_by_zone, name="Demand").reindex(zone_list).fillna(0.0)


def compute_ethylene_h2_production_ej_by_zone(scenario_dir):
    path = os.path.join(scenario_dir, dolphyn_results_folder, "Results_HSC", "HSC_h2_balance.csv")

    if not os.path.exists(path):
        raise FileNotFoundError(f"HSC_h2_balance.csv not found: {path}")

    df_raw = pd.read_csv(path, index_col=0)
    df_raw.index = df_raw.index.astype(str).str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    prod_by_zone = {}
    for base_name, zone_num, value in zip(base_names, zone_row.values, annual_row.values):
        if not base_name.startswith("Production from Ethylene Process") or pd.isna(zone_num):
            continue
        zone_name = _zone_name(zone_num)
        prod_by_zone[zone_name] = prod_by_zone.get(zone_name, 0.0) + value

    series = pd.Series(prod_by_zone, name="Steam Cracker Ethylene Prod").reindex(zone_list).fillna(0.0)
    return series * mwh_h2_p_tonne_h2 * MWH_TO_EJ


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

ethylene_df_combined, _ = read_scenario_csvs(
    f'{dolphyn_results_folder}/Results_Ethylene/Ethylene_capacity.csv'
)
ethylene_process_dfs = {}
for _scen_short, _scen_folder in dolphyn_scenario_paths.items():
    _eth_df = pd.read_csv(os.path.join(_scen_folder, "Ethylene_Resources.csv"))
    _eth_df.columns = _eth_df.columns.str.strip()
    ethylene_process_dfs[_scen_short] = _eth_df

sf_process_dfs = read_process_csvs("LFSC_Synfuel_Resources.csv")
syn_ng_process_dfs = read_process_csvs("NGSC_Syn_NG_Resources.csv")


# ---------------------------------------------------------------------
# Process Dolphyn H2 production by zone
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

hsc_zone_tables = aggregate_by_scenario_zone_category(hsc_filtered, "AnnualGeneration")

eth_h2_production_zone_tables = {}
for scen_short, scen_folder in dolphyn_scenario_paths.items():
    eth_h2_production_zone_tables[scen_short] = compute_ethylene_h2_production_ej_by_zone(scen_folder)

ethylene_df_combined["Resource_Category"] = "Steam Cracker Ethylene Consumption"

ethylene_merged_combined = merge_scenario_process_data(
    result_df=ethylene_df_combined,
    process_dfs=ethylene_process_dfs,
    result_key="Resource",
    process_key="Ethylene_Resource",
    process_cols=["tonnes_h2_p_tonne_ethylene", "tonne_ethane_p_tonne_ethylene"],
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
    * mwh_h2_p_tonne_h2
    * conversion_factor
)

ethylene_zone_tables = aggregate_by_scenario_zone_category(
    ethylene_merged_combined, "Annual_H2_Consumption_EJ"
)

_retrofit_dfs = []
for _scen_short, _scen_folder in dolphyn_scenario_paths.items():
    _scen_retrofit_df = load_ethylene_retrofit_balance(
        csv_path=os.path.join(_scen_folder, dolphyn_results_folder, "Results_Ethylene", "Ethylene_Retrofit_Balance.csv"),
        assets=H2_ASSETS,
        resource_mapping=RESOURCE_MAPPING,
    )
    _scen_retrofit_df = _scen_retrofit_df[_scen_retrofit_df["Time"] == "AnnualSum"].copy()
    _scen_retrofit_df["Scenario"] = _scen_short
    _retrofit_dfs.append(_scen_retrofit_df)

retrofit_df = pd.concat(_retrofit_dfs, ignore_index=True)
retrofit_df["Resource_Category"] = "Steam Cracker Ethylene Consumption"

ethylene_retrofit_merged_combined = merge_scenario_process_data_by_zone(
    result_df=retrofit_df,
    process_dfs=ethylene_process_dfs,
    result_key="Resource",
    process_key="Ethylene_Resource",
    result_zone_key="Zone",
    process_zone_key="Zone",
    process_cols=["tonnes_h2in_p_tonne_ethylene", "tonne_ethane_p_tonne_ethylene"],
)

ethylene_retrofit_merged_combined["Annual_H2_Consumption_EJ"] = (
    pd.to_numeric(
        ethylene_retrofit_merged_combined["Annual_ethane_Consumption"],
        errors="coerce",
    ).fillna(0.0)
    * pd.to_numeric(
        ethylene_retrofit_merged_combined["tonnes_h2in_p_tonne_ethylene"],
        errors="coerce",
    ).fillna(0.0)
    * mwh_h2_p_tonne_h2
    * conversion_factor
)

ethylene_retrofit_zone_tables = aggregate_by_scenario_zone_category(
    ethylene_retrofit_merged_combined, "Annual_H2_Consumption_EJ"
)

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

sf_zone_tables = aggregate_by_scenario_zone_category(sf_merged_combined, "Annual_H2_Consumption_EJ")

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

syn_ng_zone_tables = aggregate_by_scenario_zone_category(syn_ng_merged_combined, "Annual_H2_Consumption_EJ")

demand_zone_tables = {}
for scen_short, scen_folder in dolphyn_scenario_paths.items():
    demand_zone_tables[scen_short] = -compute_dolphyn_h2_demand_ej_by_zone(scen_folder)

dolphyn_zone_tables_by_scenario = combine_zone_tables(
    hsc_zone_tables,
    demand_zone_tables,
    sf_zone_tables,
    syn_ng_zone_tables,
    eth_h2_production_zone_tables,
    ethylene_zone_tables,
    ethylene_retrofit_zone_tables,
)

for scen in scenario_names:
    table = dolphyn_zone_tables_by_scenario[scen]
    for col in desired_order:
        if col not in table.columns:
            table[col] = 0.0
    dolphyn_zone_tables_by_scenario[scen] = table[desired_order]

    print(f"\nDolphyn H2 balance by zone — Scenario {scen} (EJ):")
    print(dolphyn_zone_tables_by_scenario[scen])


# ---------------------------------------------------------------------
# Read MACRO H2 balance by zone
# ---------------------------------------------------------------------

macro_zone_tables_by_scenario = {}

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

    macro_h2["Annual_Flow"] = (
        pd.to_numeric(macro_h2["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_h2["Plot_Category"] = macro_h2.apply(map_macro_h2_category, axis=1)
    macro_h2 = macro_h2[macro_h2["Plot_Category"].isin(desired_order)].copy()

    macro_h2["Zone"] = macro_h2["Edge"].apply(_macro_extract_zone)
    macro_h2_zoned = macro_h2[macro_h2["Zone"].notna()].copy()

    zone_table = (
        macro_h2_zoned
        .groupby(["Zone", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .reindex(zone_list)
        .fillna(0.0)
    )

    for col in desired_order:
        if col not in zone_table.columns:
            zone_table[col] = 0.0
    zone_table = zone_table[desired_order]

    macro_zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nMACRO H2 balance by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Production check: Dolphyn vs MACRO totals per category
# ---------------------------------------------------------------------

print("\nH2 by-zone D vs M check:")
for scen in scenario_names:
    if scen not in dolphyn_zone_tables_by_scenario or scen not in macro_zone_tables_by_scenario:
        continue
    for col in desired_order:
        d_total = dolphyn_zone_tables_by_scenario[scen][col].sum()
        m_total = macro_zone_tables_by_scenario[scen][col].sum()
        if abs(d_total) < 1e-6 and abs(m_total) < 1e-6:
            continue
        print(
            f"  Scenario {scen}, {col}: Dolphyn={d_total:+.4f} EJ, "
            f"MACRO={m_total:+.4f} EJ"
        )


# ---------------------------------------------------------------------
# Determine plotted scenarios and active categories
# ---------------------------------------------------------------------

plotted_scenarios = [
    s for s in scenario_names
    if s in dolphyn_zone_tables_by_scenario and s in macro_zone_tables_by_scenario
]

active_cols = [
    col for col in desired_order
    if any(
        dolphyn_zone_tables_by_scenario[s][col].abs().sum() > 1e-6 or
        macro_zone_tables_by_scenario[s][col].abs().sum() > 1e-6
        for s in plotted_scenarios
    )
]

# ---------------------------------------------------------------------------
# Interactive Plotly version — one subplot per scenario; within each
# subplot, every zone shows a stacked Dolphyn (D) bar paired with a MACRO
# (M) bar directly below it.
# ---------------------------------------------------------------------------

y_labels = []
for zone in zone_list:
    y_labels.append(f"{zone} (D)")
    y_labels.append(f"{zone} (M)")

fig_plotly = make_subplots(
    rows=len(plotted_scenarios),
    cols=1,
    shared_xaxes=True,
    subplot_titles=[f"Scenario {s}" for s in plotted_scenarios],
    vertical_spacing=0.4 / len(plotted_scenarios) if len(plotted_scenarios) > 1 else 0.1,
)

legend_shown = set()

for row_idx, scen in enumerate(plotted_scenarios, start=1):
    dolphyn_zone_table = dolphyn_zone_tables_by_scenario[scen]
    macro_zone_table = macro_zone_tables_by_scenario[scen]

    for col in active_cols:
        display_name = category_names.get(col, col)
        color = category_colors.get(col, "#333333")

        x_values = []
        for zone in zone_list:
            x_values.append(dolphyn_zone_table.loc[zone, col])
            x_values.append(macro_zone_table.loc[zone, col])

        fig_plotly.add_trace(
            go.Bar(
                name=display_name,
                y=y_labels,
                x=x_values,
                orientation="h",
                marker_color=color,
                hovertemplate="%{fullData.name}: %{x:.4f} EJ<extra></extra>",
                legendgroup=col,
                showlegend=col not in legend_shown,
            ),
            row=row_idx,
            col=1,
        )
        legend_shown.add(col)

    fig_plotly.update_yaxes(
        autorange="reversed",
        categoryorder="array",
        categoryarray=y_labels,
        row=row_idx,
        col=1,
    )
    fig_plotly.add_shape(
        dict(
            type="line", x0=0, x1=0, y0=-0.5, y1=len(y_labels) - 0.5,
            line=dict(color="black", width=1, dash="dash"),
        ),
        row=row_idx, col=1,
    )

fig_plotly.update_layout(
    barmode="relative",
    title="H2 Balance by Zone — Dolphyn vs MACRO (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(500, 45 * len(y_labels) * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "h2_byzone_d_vs_m_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
