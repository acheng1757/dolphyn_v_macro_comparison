#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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
    dolphyn_base_dir, macro_base_dir,
    dolphyn_results_folder,
)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------
# Fully manual/self-contained: dolphyn_scenario_paths and
# macro_scenario_paths are the source of truth for which scenarios this
# script compares. scenario_names is derived from them directly rather
# than imported from Step_1, so this script doesn't silently break or
# go stale whenever Step_1's shared scenario config changes.

dolphyn_scenario_paths = {
    "no_crossover": f'ethylene_only_test/{dolphyn_results_folder}/Results_Ethylene',
    "crossover": f'ethylene_only_test/{dolphyn_results_folder}/Results_Ethylene',
}

macro_scenario_paths = {
    "no_crossover": f"7_1_DOLPHYN_B2/results_001/results",
    "crossover": f"7_1_DOLPHYN_B2/results_002/results",
}

scenario_names = list(dolphyn_scenario_paths.keys())

# Ethylene flows are already in tonnes — no conversion needed for either model.

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
# z1..z9 in Network.csv = CA, NW, SW, TX, NCEN, CEN, SE, MIDAT, NE — same
# zone order used by both individual by-zone plots.
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def _dolphyn_zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


def _macro_extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name, e.g.:
        CA_F-NGin_ethylene_production_edge
        Existing_CA_F-NGin-H2out_ethylene_production_edge
        CA_F-NGin_RETROFIT_ethylene_production_edge
    System-wide edges (no zone, e.g. the global demand row) return None.
    """
    tokens = str(edge_name).split("_")
    candidates = tokens[:1]
    if tokens[:1] == ["Existing"] and len(tokens) > 1:
        candidates.append(tokens[1])

    for candidate in candidates:
        if candidate in zone_list:
            return candidate

    return None


# ---------------------------------------------------------------------
# Desired order, colors, and labels — production categories only.
#
# Ethylene demand is a single global node in the MACRO data (no per-zone
# breakdown), so demand / non-served-demand are excluded from this by-zone
# comparison entirely. Dolphyn's balance file does have zoned demand, but
# it's dropped here too so the D vs M by-zone comparison stays apples-to-
# apples (same styling as ETHYLENE_D_vs_M.py, minus the demand rows).
# ---------------------------------------------------------------------

desired_order = [
    "Existing TSC:H2",
    "Existing Capacities",
    "Ret-TSC:H2",
    "TSC:H2",
    "Ret-TSC",
    "Ret-TSC+CC90",
    "Ret-TSC+CC90:H2",
    "Ret-TSC+H2in",
    "Ret-TSC+CC90+H2in",
    "Ret-ESC",
    "Ret-TSC+H2in:CH4",
    "TSC+H2in:CH4",

    "TSC",
    "TSC+CC90",
    "TSC+CC90:H2",
    "TSC+H2in",
    "TSC+CC90+H2in",

    "ESC",

    "MS+MTO",

    "MS+MTO+CC90",
    "Dehydration NGfuel",
    "Dehydration H2fuel",
]

category_colors = {
    "TSC":                  "#e8630a",
    "Ret-TSC":              "#e8630a",   # same as TSC

    "TSC+CC90":             "#7a2e0e",
    "Ret-TSC+CC90":         "#7a2e0e",   # same as TSC+CC90

    "TSC:H2":               "#f5c518",
    "Ret-TSC:H2":           "#f5c518",   # same as TSC:H2
    "Existing TSC:H2":      "#f5c518",   # same as TSC:H2

    "MS+MTO":               "#9b59b6",
    "MS+MTO+CC90":          "#4a1a6e",

    "TSC+CC90:H2":          "#a07c00",
    "Ret-TSC+CC90:H2":      "#a07c00",   # same as TSC+CC90:H2

    "TSC+H2in":             "#3a8fd1",
    "Ret-TSC+H2in":         "#3a8fd1",   # same as TSC+H2in

    "TSC+H2in:CH4":         "#1a4f80",
    "Ret-TSC+H2in:CH4":     "#1a4f80",   # same as TSC+H2in:CH4

    "TSC+CC90+H2in":        "midnightblue",
    "Ret-TSC+CC90+H2in":    "midnightblue",   # same as TSC+CC90+H2in

    "ESC":                  "#808080",
    "Ret-ESC":              "#808080",   # same as ESC

    "Existing Capacities":  "#f5c518",   # same as TSC:H2 (existing thermal crackers)

    "Dehydration NGfuel":   "#57c46a",
    "Dehydration H2fuel":   "#1a6e30",
}

# Pattern encodes build type: "" = new build, "//" = retrofit (Ret-), ".." = existing
category_hatch = {
    "TSC":                  "",
    "Ret-TSC":              "//",
    "TSC+CC90":             "",
    "Ret-TSC+CC90":         "//",
    "TSC:H2":               "",
    "Ret-TSC:H2":           "//",
    "Existing TSC:H2":      "..",
    "MS+MTO":               "",
    "MS+MTO+CC90":          "",
    "TSC+CC90:H2":          "",
    "Ret-TSC+CC90:H2":      "//",
    "TSC+H2in":             "",
    "Ret-TSC+H2in":         "//",
    "TSC+H2in:CH4":         "",
    "Ret-TSC+H2in:CH4":     "//",
    "TSC+CC90+H2in":        "",
    "Ret-TSC+CC90+H2in":    "//",
    "ESC":                  "",
    "Ret-ESC":              "//",
    "Existing Capacities":  "..",
    "Dehydration NGfuel":   "",
    "Dehydration H2fuel":   "",
}

label_map = {
    "TSC":                  "TSC",
    "Ret-TSC":              "Ret-TSC",

    "TSC+CC90":             "TSC+CC90",
    "Ret-TSC+CC90":         "Ret-TSC+CC90",

    "TSC:H2":               "TSC:H2",
    "Ret-TSC:H2":          "Ret-TSC:H2",

    "MS+MTO":               "MS+MTO",
    "MS+MTO+CC90":          "MS+MTO+CC90",

    "TSC+CC90:H2":          "TSC+CC90:H2",
    "Ret-TSC+CC90:H2":     "Ret-TSC+CC90:H2",

    "TSC+H2in":             "TSC+H2in",
    "Ret-TSC+H2in":         "Ret-TSC+H2in",

    "TSC+CC90+H2in":        "TSC+CC90+H2in",
    "Ret-TSC+CC90+H2in":    "Ret-TSC+CC90+H2in",

    "TSC+H2in:CH4":         "TSC+H2in:CH4",
    "Ret-TSC+H2in:CH4":     "Ret-TSC+H2in:CH4",

    "Existing TSC:H2":  "Existing TSC:H2",

    "Dehydration NGfuel":   "Dehydration NGfuel",
    "Dehydration H2fuel":   "Dehydration H2fuel",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC", # confirm grouping
    "Existing Capacities":  "Existing Capacities",
}

# ---------------------------------------------------------------------
# Dolphyn: resource -> plot category mapping (same as ETHYLENE_D_vs_M.py)
# ---------------------------------------------------------------------

RESOURCE_CATEGORY_MAP = {
    "TSC":            "TSC",
    "TSC+CC90": "TSC+CC90",
    "TSC:H2":            "TSC:H2", # not sure about this one
    "TSC: H2":            "TSC:H2", # not sure about this one
    "Bio-eth+CC88:NG":            "Dehydration NGfuel",
    "Bio-eth+CC88:H2":            "Dehydration H2fuel",
    "MS+MTO":            "MS+MTO",
    "MS+MTO+CC90":            "MS+MTO+CC90",
    "TSC+CC90:H2":            "TSC+CC90:H2", # mapping based on what Chaitanya said
    "TSC+CC90: H2":            "TSC+CC90:H2", # mapping based on what Chaitanya said
    "TSC+H2in":            "TSC+H2in",
    "TSC+CC90+H2in":            "TSC+H2in:CH4",
    "ESC":            "ESC",
    "Existing Capacities":            "Existing Capacities",
    "TSC+H2in:CH4":         "TSC+H2in:CH4",
    "TSC+H2in: CH4":         "TSC+H2in:CH4",
}


def categorize_ethylene_resource(resource):
    return RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None)


# ---------------------------------------------------------------------
# Dolphyn: load production by zone from Ethylene_Balance.csv /
# Ethylene_Retrofit_Balance.csv, keeping each (Resource, Zone) pair as its
# own row instead of summing across zones.
# ---------------------------------------------------------------------

def load_ethylene_production_by_zone(balance_path, scenario):
    df_raw = pd.read_csv(balance_path, index_col=0)
    df_raw.index = df_raw.index.str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    df = pd.DataFrame({
        "Resource": base_names,
        "Zone": zone_row.values,
        "Annual_Ethylene_Production": annual_row.values,
    })
    df = df[df["Zone"].notna()].copy()
    df["Zone"] = df["Zone"].apply(_dolphyn_zone_name)

    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    df = df[df["Plot_Category"].notna()].copy()
    df["Scenario"] = scenario

    return df[["Scenario", "Zone", "Plot_Category", "Annual_Ethylene_Production"]]


def load_ethylene_production_retrofit_by_zone(balance_retrofit_path, scenario):
    df_raw = pd.read_csv(balance_retrofit_path, header=0, index_col=0)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw.index = df_raw.index.astype(str).str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    df = pd.DataFrame({
        "Resource": base_names,
        "Zone": zone_row.values,
        "Annual_Ethylene_Production": annual_row.values,
    })
    df = df[df["Zone"].notna()].copy()
    df["Zone"] = df["Zone"].apply(_dolphyn_zone_name)

    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(
        lambda r: "Ret-" + categorize_ethylene_resource(r)
        if categorize_ethylene_resource(r) is not None
        else None
    )
    df = df[df["Plot_Category"].notna()].copy()
    df["Scenario"] = scenario

    return df[["Scenario", "Zone", "Plot_Category", "Annual_Ethylene_Production"]]


# ---------------------------------------------------------------------
# Dolphyn loading loop
# ---------------------------------------------------------------------

dolphyn_zone_tables_by_scenario = {}

for scen_short, scen_path in dolphyn_scenario_paths.items():
    results_dir = os.path.join(dolphyn_base_dir, scen_path)
    balance_path = os.path.join(results_dir, "Ethylene_Balance_newv.csv")
    balance_retrofit_path = os.path.join(results_dir, "Ethylene_Retrofit_Balance_newv.csv")

    if not os.path.exists(balance_path):
        print(f"Warning: Ethylene_Balance_newv.csv not found: {balance_path}")
        continue

    if not os.path.exists(balance_retrofit_path):
        print(f"Warning: Ethylene_Retrofit_Balance_newv.csv not found: {balance_retrofit_path}")
        continue

    prod_df = load_ethylene_production_by_zone(balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit_by_zone(balance_retrofit_path, scen_short)

    scen_table = pd.concat([prod_df, prod_df_retrofit], ignore_index=True)

    zone_table = (
        scen_table
        .groupby(["Zone", "Plot_Category"])["Annual_Ethylene_Production"]
        .sum()
        .unstack()
        .reindex(zone_list)
        .fillna(0.0)
    )

    for col in desired_order:
        if col not in zone_table.columns:
            zone_table[col] = 0.0
    zone_table = zone_table[desired_order]

    dolphyn_zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nDolphyn ethylene production by zone — Scenario {scen_short} (t/yr):")
    print(zone_table)


# ---------------------------------------------------------------------
# MACRO: load production by zone from annual_flows_balance_Ethylene.csv
# ---------------------------------------------------------------------

macro_zone_tables_by_scenario = {}
macro_unzoned_production_by_scenario = {}

for scen_short, scen_path in macro_scenario_paths.items():
    macro_eth_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethylene.csv",
    )

    if not os.path.exists(macro_eth_path):
        print(f"Warning: MACRO ethylene balance file not found: {macro_eth_path}")
        continue

    macro_eth = pd.read_csv(macro_eth_path)
    macro_eth.columns = macro_eth.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_eth.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_eth_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_eth.columns.tolist()}"
        )

    macro_eth["Annual_Flow"] = pd.to_numeric(
        macro_eth["Annual_Flow"], errors="coerce"
    ).fillna(0.0)

    macro_eth["Plot_Category"] = macro_eth["Category"]
    macro_eth["Zone"] = macro_eth["Edge"].apply(_macro_extract_zone)

    # Keep only zoned production rows (drops the global demand/NSD rows,
    # since ethylene demand has no per-zone breakdown in this dataset).
    macro_eth_zoned = macro_eth[
        macro_eth["Zone"].notna() & macro_eth["Plot_Category"].isin(desired_order)
    ].copy()

    # Track production-category rows that didn't get a zone assigned, so a
    # coverage gap doesn't silently disappear from the by-zone tables.
    unzoned_production = macro_eth[
        macro_eth["Zone"].isna() &
        macro_eth["Plot_Category"].isin(desired_order)
    ]
    macro_unzoned_production_by_scenario[scen_short] = unzoned_production["Annual_Flow"].sum()

    zone_table = (
        macro_eth_zoned
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

    print(f"\nMACRO ethylene production by zone — Scenario {scen_short} (t/yr):")
    print(zone_table)


# ---------------------------------------------------------------------
# Production check: Dolphyn vs MACRO totals, and MACRO zone-coverage gaps
# ---------------------------------------------------------------------

print("\nEthylene by-zone production check:")
for scen in scenario_names:
    if scen not in dolphyn_zone_tables_by_scenario or scen not in macro_zone_tables_by_scenario:
        continue
    dolphyn_total = dolphyn_zone_tables_by_scenario[scen].to_numpy().sum()
    macro_total = macro_zone_tables_by_scenario[scen].to_numpy().sum()
    unzoned_total = macro_unzoned_production_by_scenario.get(scen, 0.0)
    print(
        f"  Scenario {scen}: Dolphyn total = {dolphyn_total:,.4f} t/yr, "
        f"MACRO total = {macro_total:,.4f} t/yr, "
        f"diff = {dolphyn_total - macro_total:,.4f} t/yr"
    )
    if abs(unzoned_total) >= 1.0:
        print(f"    WARNING: {unzoned_total:,.4f} t/yr of MACRO production could not be assigned to a zone")


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
        dolphyn_zone_tables_by_scenario[s][col].abs().sum() > 1.0 or
        macro_zone_tables_by_scenario[s][col].abs().sum() > 1.0
        for s in plotted_scenarios
    )
]

# ---------------------------------------------------------------------------
# Interactive Plotly version — one subplot per scenario; within each
# subplot, every zone shows a stacked Dolphyn (D) bar paired with a MACRO
# (M) bar directly below it.
# ---------------------------------------------------------------------------

_plotly_hatch_map = {"//": "/", "..": "."}

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
        display_name = label_map.get(col, col)
        color = category_colors.get(col, "#333333")
        pattern_shape = _plotly_hatch_map.get(category_hatch.get(col, ""), "")

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
                marker_pattern_shape=pattern_shape,
                marker_pattern_fgcolor="white",
                marker_pattern_fillmode="overlay",
                hovertemplate="%{fullData.name}: %{x:,.0f} t/yr<extra></extra>",
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
    title="Ethylene Production by Zone — Dolphyn vs MACRO (t/yr)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(500, 45 * len(y_labels) * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="t/yr", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ethylene_byzone_d_vs_m_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
