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
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

dolphyn_scenario_paths = {
    "ethylene_only_test": f'ethylene_only_test/{dolphyn_results_folder}/Results_Ethylene',
}

# Ethylene_Balance_newv.csv / Ethylene_Retrofit_Balance_newv.csv AnnualSum values
# are in tonnes/year already.

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
# z1..z9 in Network.csv = CA, NW, SW, TX, NCEN, CEN, SE, MIDAT, NE — same
# zone order used by the MACRO by-zone plots.
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def _zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


# ---------------------------------------------------------------------
# Desired order, colors, and labels (same styling as ETHYLENE_Dolphyn.py)
# ---------------------------------------------------------------------

desired_order = [
    "TSC",
    "Ret-TSC",
    "Existing Capacities",

    "TSC+CC90",
    "Ret-TSC+CC90",

    "TSC:H2",
    "Ret-TSC:H2",

    "MS+MTO",

    "MS+MTO+CC90",

    "TSC+CC90:H2",
    "Ret-TSC+CC90:H2",

    "TSC+H2in",
    "Ret-TSC+H2in",

    "TSC+CC90+H2in",
    "Ret-TSC+CC90+H2in",

    "ESC",
    "Ret-ESC",

    "TSC+H2in:CH4",
    "Ret-TSC+H2in:CH4",

    "Dehydration NGfuel",
    "Dehydration H2fuel",
    "Ethylene Demand",
]

category_colors = {
    "TSC":                  "#e8630a",   # vivid orange
    "Ret-TSC":              "#f4a86a",   # light orange

    "TSC+CC90":             "#7a2e0e",   # deep brick
    "Ret-TSC+CC90":         "#b5603a",   # mid brick

    "TSC:H2":               "#f5c518",   # bright gold (H2out co-product)
    "Ret-TSC:H2":          "#fae27a",   # light gold

    "MS+MTO":               "#9b59b6",   # purple (synthetic)
    "MS+MTO+CC90":          "#4a1a6e",   # deep purple

    "TSC+CC90:H2":          "#a07c00",   # dark gold (CC90 + H2out)
    "Ret-TSC+CC90:H2":     "#d4b840",   # mid gold

    "TSC+H2in":             "#3a8fd1",   # sky blue (H2fuel input)
    "Ret-TSC+H2in":         "#85c4ec",   # light sky blue

    "TSC+H2in:CH4":         "#1a4f80",   # navy (H2fuel + CH4out)
    "Ret-TSC+H2in:CH4":     "#4a7faf",   # mid navy

    "TSC+CC90+H2in":        "midnightblue",   # navy (CC90 + H2fuel) — same family
    "Ret-TSC+CC90+H2in":    "navy",   # mid navy

    "Existing Capacities":  "#cccccc",   # light gray
    "ESC":              "#a0a0a0",   # mid gray
    "Ret-ESC":              "#a0a0a0",   # mid gray

    "Dehydration NGfuel":   "#57c46a",   # medium green
    "Dehydration H2fuel":   "#1a6e30",   # dark green
    "Ethylene Demand":      "#5a6fa8",   # slate blue
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

    "Existing Capacities":  "Existing Capacities",

    "Dehydration NGfuel":   "Dehydration NGfuel",
    "Dehydration H2fuel":   "Dehydration H2fuel",
    "Ethylene Demand":      "Ethylene Demand",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC",
}

# used to categorize the label directly in the CSV
RESOURCE_CATEGORY_MAP = {
    "TSC":            "TSC",
    "TSC+CC90": "TSC+CC90",
    "TSC:H2":            "TSC:H2",
    "TSC: H2":            "TSC:H2",
    "Bio-eth+CC88:NG":            "Dehydration NGfuel",
    "Bio-eth+CC88:H2":            "Dehydration H2fuel",
    "MS+MTO":            "MS+MTO",
    "MS+MTO+CC90":            "MS+MTO+CC90",
    "TSC+CC90:H2":            "TSC+CC90:H2",
    "TSC+CC90: H2":            "TSC+CC90:H2",
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
# Load production from Ethylene_Balance.csv for EXISTING + NEW BUILD ASSETS,
# keeping each (Resource, Zone) pair as its own row instead of summing
# across zones.
# ---------------------------------------------------------------------
def load_ethylene_production_by_zone(balance_path, scenario):
    df_raw = pd.read_csv(balance_path, index_col=0)
    df_raw.index = df_raw.index.str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    # Resource columns repeat per zone with pandas' auto-dedup suffix (.1, .2, …)
    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    df = pd.DataFrame({
        "Resource": base_names,
        "Zone": zone_row.values,
        "Annual_Ethylene_Production": annual_row.values,
    })
    df = df[df["Zone"].notna()].copy()
    df["Zone"] = df["Zone"].apply(_zone_name)

    # Zero out optimiser noise
    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    df = df[df["Plot_Category"].notna()].copy()
    df["Scenario"] = scenario

    return df[["Scenario", "Zone", "Plot_Category", "Annual_Ethylene_Production"]]


# ---------------------------------------------------------------------
# Load production from Ethylene_Retrofit_Balance.csv for RETROFITTED ASSETS,
# again keeping the per-zone breakdown.
# ---------------------------------------------------------------------
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
    df["Zone"] = df["Zone"].apply(_zone_name)

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
# Load per-zone demand from Ethylene_Balance.csv
# ---------------------------------------------------------------------
def load_ethylene_demand_by_zone(balance_path, scenario):
    """
    Return {zone_name: demand value} (negative, tonnes/year) for every
    column whose base name contains "demand".
    """
    df_raw = pd.read_csv(balance_path, index_col=0)
    df_raw.index = df_raw.index.str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    demand_cols = [c for c in df_raw.columns if "demand" in c.lower()]
    if not demand_cols:
        print(f"  Warning: no demand columns found in {balance_path}")
        return {}

    demand_by_zone = {}
    for col in demand_cols:
        zone_num = zone_row.get(col)
        if pd.isna(zone_num):
            continue
        demand_by_zone[_zone_name(zone_num)] = float(annual_row[col])

    return demand_by_zone


# ---------------------------------------------------------------------
# Main loading loop
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}

for scen_short, scen_path in dolphyn_scenario_paths.items():
    results_dir = os.path.join(dolphyn_base_dir, scen_path)
    balance_path = os.path.join(results_dir, "Ethylene_Balance_newv.csv")
    balance_retrofit_path = os.path.join(results_dir, "Ethylene_Retrofit_Balance_newv.csv")

    if not os.path.exists(balance_path):
        print(f"Warning: Ethylene_Balance.csv not found: {balance_path}")
        continue

    if not os.path.exists(balance_retrofit_path):
        print(f"Warning: Ethylene_Retrofit_Balance.csv not found: {balance_retrofit_path}")
        continue

    prod_df = load_ethylene_production_by_zone(balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit_by_zone(balance_retrofit_path, scen_short)

    demand_by_zone = load_ethylene_demand_by_zone(balance_path, scen_short)
    demand_df = pd.DataFrame([
        {"Scenario": scen_short, "Zone": zone, "Plot_Category": "Ethylene Demand",
         "Annual_Ethylene_Production": value}
        for zone, value in demand_by_zone.items()
    ])

    scen_table = pd.concat([prod_df, prod_df_retrofit, demand_df], ignore_index=True)

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

    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nDolphyn ethylene balance by zone — Scenario {scen_short} (tonnes/year):")
    print(zone_table)


# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario, across zones
# ---------------------------------------------------------------------
print("\nEthylene balance check (by zone, summed across zones):")
for scen, zone_table in zone_tables_by_scenario.items():
    totals = zone_table.sum(axis=0)
    total_positive = totals[totals > 0].sum()
    total_negative = totals[totals < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} tonnes, "
        f"Demand={total_negative:+.4f} tonnes, "
        f"Net={net:+.4f} tonnes  [{status}]"
    )


# ---------------------------------------------------------------------
# Determine plotted scenarios and active categories
# ---------------------------------------------------------------------

plotted_scenarios = list(zone_tables_by_scenario.keys())

# Only keep columns with non-zero values in at least one scenario, in desired order
active_cols = [
    col for col in desired_order
    if any(zone_tables_by_scenario[s][col].abs().sum() > 1.0 for s in plotted_scenarios)
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
        display_name = label_map.get(col, col)
        color = category_colors.get(col, "#333333")

        fig_plotly.add_trace(
            go.Bar(
                name=display_name,
                y=zone_list,
                x=plot_df[col].tolist(),
                orientation="h",
                marker_color=color,
                hovertemplate="%{fullData.name}: %{x:.2f} tonnes<extra></extra>",
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
    title="Ethylene Balance by Zone (t/yr)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="tonnes", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ethylene_byzone_dolphyn_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
