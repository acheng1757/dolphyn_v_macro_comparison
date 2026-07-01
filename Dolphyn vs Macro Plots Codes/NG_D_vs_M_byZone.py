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
    macro_base_dir, dolphyn_results_folder,
)

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# Dolphyn NG_Balance values are treated as MMBtu (same as NG_D_vs_M.py).
MMBTU_TO_EJ = 0.293071 * 3.6e-9
# MACRO annual_flow values are treated as MWh.
MWH_TO_EJ = 3.6e-9

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------
# Fully manual/self-contained: dolphyn_scenario_paths and
# macro_scenario_paths are the source of truth for which scenarios this
# script compares (same values as NG_D_vs_M.py). scenario_names is
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


def _dolphyn_zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


def _macro_extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name (same logic as
    NG_Macro_byZone.py's extract_zone).

    Production/consumption edges put the zone first:
        CEN_Bio_NG_Herb_natgas_edge
        Existing_CEN_F-NGin-H2out_natgas_consumption_edge
    Demand-sector edges put the zone last:
        NaturalGas_MW_NW
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


def map_macro_ng_category(row):
    """
    Map MACRO annual_flows_balance_NG.csv rows to NG balance categories
    (same as NG_Macro.py / NG_Macro_byZone.py).
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    if sector == "Demand":
        return "NG_Demand"

    if category == "NG Fossil Upstream":
        return "Conventional_NG"

    if sector == "Synthetic fuels" and category == "S-NG":
        return "Syn_NG"

    if sector == "Power":
        return "Power"

    if sector == "Hydrogen":
        return "H2"

    if sector == "CO2":
        return "CSC"

    if sector == "Bioenergy":
        return "BESC"

    if sector == "Ethylene":
        try:
            flow = float(row.get("Annual_Flow", 0.0))
        except (TypeError, ValueError):
            flow = 0.0
        return "Ethylene Production" if flow >= 0 else "Ethylene Consumption"

    if sector == "Ethanol":
        return "Ethanol"

    return None


# ---------------------------------------------------------------------
# Desired order, colors, and labels — merged Dolphyn + MACRO category
# set (same as the updated NG_D_vs_M.py), minus Non-Served Demand,
# which has no per-zone breakdown on the MACRO side.
# ---------------------------------------------------------------------

desired_order = [
    "NG_Demand",
    "Ethylene Production",
    "Ethylene Consumption",
    "Power",
    "H2",
    "CSC",
    "BESC",
    "Syn_NG",
    "Bio_NG",
    "Conventional_NG",
    "Ethanol",
]

category_colors = {
    "Syn_NG": "#e8905a",
    "Bio_NG": "mediumseagreen",
    "Conventional_NG": "#c0504d",
    "NG_Demand": "bisque",
    "Power": "orange",
    "H2": "deepskyblue",
    "CSC": "darkblue",
    "BESC": "seagreen",
    "Ethylene Production": "#e8630a",
    "Ethylene Consumption": "#7a2e0e",
    "Ethanol": "#d4a017",
}

category_names = {
    "Syn_NG": "Syn. NG",
    "Bio_NG": "Bio NG",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC",
    "BESC": "Bio NG Prod.",
    "Ethylene Production": "Ethylene Sector (Production)",
    "Ethylene Consumption": "Ethylene Sector (Consumption)",
    "Ethanol": "Ethanol Sector",
}


# ---------------------------------------------------------------------
# Dolphyn: load NG_Balance.csv by zone, keeping each (Resource, Zone)
# pair as its own row instead of summing across zones (same approach as
# NG_Dolphyn_byZone.py).
# ---------------------------------------------------------------------

dolphyn_columns_of_interest = [
    "Syn_NG", "Bio_NG", "Conventional_NG", "NG_Demand", "Power", "H2",
    "CSC", "BESC", "Ethylene Consumption", "Ethylene Production",
]


def load_ng_balance_by_zone(path, scenario):
    df_raw = pd.read_csv(path, index_col=0)
    df_raw.index = df_raw.index.astype(str).str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    df = pd.DataFrame({
        "Resource": base_names,
        "Zone": zone_row.values,
        "Value": annual_row.values * MMBTU_TO_EJ,
    })
    df = df[df["Zone"].notna()].copy()
    df["Zone"] = df["Zone"].apply(_dolphyn_zone_name)
    df = df[df["Resource"].isin(dolphyn_columns_of_interest)].copy()

    zone_table = (
        df.groupby(["Zone", "Resource"])["Value"]
        .sum()
        .unstack()
        .reindex(zone_list)
        .fillna(0.0)
    )

    for col in desired_order:
        if col not in zone_table.columns:
            zone_table[col] = 0.0
    zone_table = zone_table[desired_order]

    return zone_table


dolphyn_zone_tables_by_scenario = {}

for scen_short, scen_folder in dolphyn_scenario_paths.items():
    path = os.path.join(scen_folder, dolphyn_results_folder, "Results_NG", "NG_Balance.csv")

    if not os.path.exists(path):
        print(f"Warning: Dolphyn NG_Balance.csv not found: {path}")
        continue

    zone_table = load_ng_balance_by_zone(path, scen_short)
    dolphyn_zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nDolphyn NG balance by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# MACRO: read NG balance by zone from annual_flows_balance_NG.csv
# ---------------------------------------------------------------------

macro_zone_tables_by_scenario = {}

for scen_short, scen_path in macro_scenario_paths.items():
    macro_ng_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_NG.csv",
    )

    if not os.path.exists(macro_ng_path):
        print(f"Warning: MACRO NG balance file not found: {macro_ng_path}")
        continue

    macro_ng = pd.read_csv(macro_ng_path)
    macro_ng.columns = macro_ng.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_ng.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_ng_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_ng.columns.tolist()}"
        )

    macro_ng["Annual_Flow"] = (
        pd.to_numeric(macro_ng["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_ng["Plot_Category"] = macro_ng.apply(map_macro_ng_category, axis=1)
    macro_ng = macro_ng[macro_ng["Plot_Category"].isin(desired_order)].copy()

    macro_ng["Zone"] = macro_ng["Edge"].apply(_macro_extract_zone)
    macro_ng_zoned = macro_ng[macro_ng["Zone"].notna()].copy()

    zone_table = (
        macro_ng_zoned
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

    print(f"\nMACRO NG balance by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Production check: Dolphyn vs MACRO totals per category
# ---------------------------------------------------------------------

print("\nNG by-zone D vs M check:")
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
    title="NG Balance by Zone — Dolphyn vs MACRO (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(500, 45 * len(y_labels) * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ng_byzone_d_vs_m_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
