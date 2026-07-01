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
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_results_folder

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ
mwh_h2_p_tonne_h2 = 39.39

dolphyn_scenario_paths = {
    "no_crossover": "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn/ethylene_only_test/",
}

scenario_names = list(dolphyn_scenario_paths.keys())

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
# z1..z9 in Network.csv = CA, NW, SW, TX, NCEN, CEN, SE, MIDAT, NE — same
# zone order used by the ethylene by-zone plots.
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def _zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


# ---------------------------------------------------------------------
# Helper functions (unchanged from H2_Dolphyn.py — these already carry a
# Zone column through every merge; see load_ethylene_retrofit_balance and
# merge_scenario_process_data_by_zone below)
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


H2_ASSETS = ["TSC+H2in:CH4", "TSC+H2in", "MS+MTO+CC90", "Bio-eth+CC88:H2"]

# Maps CSV asset names → Ethylene_Resource keys in the process parameter files
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
    """
    Parse Ethylene_Retrofit_Balance.csv into a long-form DataFrame suitable
    for merging into the ethylene aggregation pipeline. Returns a Zone
    column (int) alongside Resource/AnnualSum/Annual_ethane_Consumption.
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
    """
    Like merge_scenario_process_data but joins on both resource name and zone,
    needed for retrofit assets where parameters vary by zone.
    """
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


# ---------------------------------------------------------------------
# Zone-aware aggregation (new — replaces H2_Dolphyn.py's
# aggregate_by_scenario_category, which grouped by Scenario+Resource_Category
# only and discarded the Zone column)
# ---------------------------------------------------------------------

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
    DataFrame per scenario, merging duplicate column names by summation
    (mirrors H2_Dolphyn.py's `combined_data.T.groupby(level=0).sum().T`).
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


# ---------------------------------------------------------------------
# Zone-aware H2 demand (new — replaces H2_Dolphyn.py's
# compute_dolphyn_h2_demand_ej, which summed all Load_H2_tonne_per_hr_z*
# columns into a single global number)
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# Zone-aware ethylene H2 production (new — replaces H2_Dolphyn.py's
# compute_ethylene_h2_production_ej, which summed all "Production from
# Ethylene Process" columns together)
# ---------------------------------------------------------------------

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
_eth_df = pd.read_csv(os.path.join(dolphyn_scenario_paths[scenario_names[0]], "Ethylene_Resources.csv"))
_eth_df.columns = _eth_df.columns.str.strip()
ethylene_process_dfs = {scenario_names[0]: _eth_df}

# ---------------------------------------------------------------------
# Load Dolphyn process-parameter files
# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------
# Process Dolphyn H2 production from Ethylene, by zone
# ---------------------------------------------------------------------

eth_h2_production_zone_tables = {}
for scen_short, scen_folder in dolphyn_scenario_paths.items():
    eth_h2_production_zone_tables[scen_short] = compute_ethylene_h2_production_ej_by_zone(scen_folder)

# ---------------------------------------------------------------------
# Process Dolphyn Ethylene H2 consumption from new build assets, by zone
# ---------------------------------------------------------------------

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

# ---------------------------------------------------------------------
# Process Dolphyn Ethylene H2 consumption from retrofit assets, by zone
# ---------------------------------------------------------------------

retrofit_df = load_ethylene_retrofit_balance(
    csv_path=os.path.join(dolphyn_scenario_paths[scenario_names[0]], dolphyn_results_folder, "Results_Ethylene", "Ethylene_Retrofit_Balance.csv"),
    assets=H2_ASSETS,
    resource_mapping=RESOURCE_MAPPING,
)
retrofit_df = retrofit_df[retrofit_df["Time"] == "AnnualSum"].copy()
retrofit_df["Scenario"] = scenario_names[0]
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

# ---------------------------------------------------------------------
# Process Dolphyn synthetic liquid fuels H2 consumption, by zone
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

sf_zone_tables = aggregate_by_scenario_zone_category(sf_merged_combined, "Annual_H2_Consumption_EJ")

# ---------------------------------------------------------------------
# Process Dolphyn synthetic natural gas H2 consumption, by zone
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

syn_ng_zone_tables = aggregate_by_scenario_zone_category(syn_ng_merged_combined, "Annual_H2_Consumption_EJ")

# ---------------------------------------------------------------------
# Dolphyn H2 demand by zone
# ---------------------------------------------------------------------

demand_zone_tables = {}
for scen_short, scen_folder in dolphyn_scenario_paths.items():
    demand_zone_tables[scen_short] = -compute_dolphyn_h2_demand_ej_by_zone(scen_folder)

print("Dolphyn weighted H2 demand by zone (EJ):")
for scen in scenario_names:
    print(f"  Scenario {scen}:")
    print(demand_zone_tables[scen])


# ---------------------------------------------------------------------
# Combine Dolphyn H2 balance by zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = combine_zone_tables(
    hsc_zone_tables,
    demand_zone_tables,
    sf_zone_tables,
    syn_ng_zone_tables,
    eth_h2_production_zone_tables,
    ethylene_zone_tables,
    ethylene_retrofit_zone_tables,
)

desired_order = [
    "Steam Cracker Ethylene Prod",
    "Demand",
    "Synthetic FT",
    "Synthetic NG",
    "Electrolyzer",
    "NG CCS H2",
    "BECCS H2",
    "Steam Cracker Ethylene Consumption",
]

for scen in scenario_names:
    table = zone_tables_by_scenario[scen]
    for col in desired_order:
        if col not in table.columns:
            table[col] = 0.0
    zone_tables_by_scenario[scen] = table[desired_order]


# ---------------------------------------------------------------------
# Print balance tables for checking
# ---------------------------------------------------------------------

for scen in scenario_names:
    print(f"\nDolphyn H2 balance by zone — Scenario {scen} (EJ):")
    print(zone_tables_by_scenario[scen])


# ---------------------------------------------------------------------
# Print net H2 balance per zone (production + and consumption -) before plotting
# ---------------------------------------------------------------------

print("\nH2 Net Balance Summary by zone (EJ):")
for scen in scenario_names:
    print(f"\nScenario: {scen}")
    print(f"{'Zone':<10} {'Production (+)':<18} {'Consumption (-)':<18} {'Net Balance':<12}")
    print("-" * 60)
    for zone, row in zone_tables_by_scenario[scen].iterrows():
        production = row[row > 0].sum()
        consumption = row[row < 0].sum()
        net = production + consumption
        print(f"{zone:<10} {production:<18.4f} {consumption:<18.4f} {net:<12.4f}")


# ---------------------------------------------------------------------
# Plot settings
# ---------------------------------------------------------------------

category_colors = {
    "Electrolyzer": "lightgreen",
    "NG CCS H2": "deepskyblue",
    "BECCS H2": "seagreen",
    "Synthetic FT": "purple",
    "Synthetic NG": "violet",
    "Steam Cracker Ethylene Prod": "red",
    "Steam Cracker Ethylene Consumption": "orange",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Steam Cracker Ethylene Prod": "Steam Cracker Ethylene Prod",
    "Steam Cracker Ethylene Consumption": "Steam Cracker Ethylene Consumption",
    "Demand": "Demand",
}


# ---------------------------------------------------------------------
# Determine plotted scenarios and active categories
# ---------------------------------------------------------------------

plotted_scenarios = list(zone_tables_by_scenario.keys())

active_cols = [
    col for col in desired_order
    if any(zone_tables_by_scenario[s][col].abs().sum() > 1e-6 for s in plotted_scenarios)
]

# ---------------------------------------------------------------------------
# Interactive Plotly version — one subplot per scenario, hover for details
# ---------------------------------------------------------------------------

fig_plotly = make_subplots(
    rows=len(plotted_scenarios),
    cols=1,
    shared_xaxes=True,
    subplot_titles=[f"Scenario {s}" for s in plotted_scenarios],
    vertical_spacing=0.4 / len(plotted_scenarios) if len(plotted_scenarios) > 1 else 0.1,
)

legend_shown = set()

for row_idx, scen in enumerate(plotted_scenarios, start=1):
    plot_df = zone_tables_by_scenario[scen][active_cols]

    for col in active_cols:
        display_name = category_names.get(col, col)
        color = category_colors.get(col, "#333333")

        fig_plotly.add_trace(
            go.Bar(
                name=display_name,
                y=zone_list,
                x=plot_df[col].tolist(),
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

    fig_plotly.update_yaxes(autorange="reversed", row=row_idx, col=1)
    fig_plotly.add_shape(
        dict(
            type="line", x0=0, x1=0, y0=-0.5, y1=len(zone_list) - 0.5,
            line=dict(color="black", width=1, dash="dash"),
        ),
        row=row_idx, col=1,
    )

fig_plotly.update_layout(
    barmode="relative",
    title="H2 Balance by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "h2_byzone_dolphyn_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
