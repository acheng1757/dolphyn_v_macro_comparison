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
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

MWH_TO_EJ = 3.6e-9

# ---------------------------------------------------------------------
# Desired order, colors, and labels (same as Power_Macro.py, minus
# Non-Served Demand, which has no per-zone breakdown in this dataset)
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "H2 Production",
    "Sorbent DAC Input",
    "Bioenergy Input",
    "Ethylene Input",
    "Ethanol Input",
    "Synthetic FT",
    "Synthetic NG",
    "Ethanol Upgrading",
    "Hydro",
    "Nuclear",
    "NG",
    "NG CCS",
    "Solar",
    "Wind",
]

category_colors = {
    "Hydro": "steelblue",
    "Nuclear": "red",
    "NG": "#c0504d",
    "NG CCS": "silver",
    "Solar": "gold",
    "Wind": "dodgerblue",
    "Sorbent DAC Input": "darkblue",
    "Bioenergy Input": "seagreen",
    "Ethylene Input": "#e8630a",
    "Ethanol Input": "#d4a017",
    "Ethanol Upgrading": "#c8b040",
    "Synthetic NG": "#e8905a",
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
    "Ethanol Upgrading": "Eth. Upgrading",
    "Hydro": "Hydro",
    "Nuclear": "Nuclear",
    "NG": "NG",
    "NG CCS": "NG CCS",
    "Solar": "Solar",
    "Wind": "Wind",
}

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name.

    Production/consumption edges put the zone first:
        CA_Electrolyzer_elec_edge
    Demand-sector edges put the zone last:
        Electricity_MW_NW

    Global/system-wide edges have no zone and return None.
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


# ---------------------------------------------------------------------
# MACRO Power balance mapping (same as Power_Macro.py)
# ---------------------------------------------------------------------

def map_macro_power_category(row):
    """
    Map MACRO annual_flows_balance_Power.csv rows to plotting categories.

    Small MACRO-only categories intentionally excluded:
      - storage losses
      - H2 turbines (H2 CCGT, H2 OCGT)
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    if sector == "Demand":
        return "Demand"

    if sector == "Power":
        if category in ["Hydro", "Nuclear", "NG", "NG CCS", "Solar", "Wind"]:
            return category

        if category in ["Battery", "H2 CCGT", "H2 OCGT"]:
            return None

        return None

    if sector == "Hydrogen":
        return "H2 Production"

    if sector == "CO2":
        return "Sorbent DAC Input"

    if sector == "Bioenergy":
        return "Bioenergy Input"

    if sector == "Ethanol":
        return "Ethanol Input"

    if sector == "Ethylene":
        return "Ethylene Input"

    if sector == "Synthetic fuels":
        if category == "S-NG":
            return "Synthetic NG"

        if category in ["S-J", "S-J-CC99", "S-J-99"]:
            return "Synthetic FT"

        return "Synthetic FT"

    if sector == "Ethanol Upgrading":
        return "Ethanol Upgrading"

    return None


# ---------------------------------------------------------------------
# Read MACRO Power balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
system_level_totals_by_scenario = {}

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

    macro_power["Annual_Flow"] = (
        pd.to_numeric(macro_power["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_power["Plot_Category"] = macro_power.apply(map_macro_power_category, axis=1)
    macro_power = macro_power[macro_power["Plot_Category"].isin(desired_order)].copy()

    system_level_totals_by_scenario[scen_short] = (
        macro_power.groupby("Plot_Category")["Annual_Flow"].sum()
        .reindex(desired_order)
        .fillna(0.0)
    )

    macro_power["Zone"] = macro_power["Edge"].apply(extract_zone)
    macro_power_zoned = macro_power[macro_power["Zone"].notna()].copy()

    zone_table = (
        macro_power_zoned
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

    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nElectricity production/consumption by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Plot — Plotly only, one subplot per scenario, zones as horizontal bars
# ---------------------------------------------------------------------

plotted_scenarios = [s for s in scenario_names if s in zone_tables_by_scenario]

active_cols = [
    col for col in desired_order
    if any(
        zone_tables_by_scenario[s][col].abs().sum() > 1e-6
        for s in plotted_scenarios
    )
]

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
        fig_plotly.add_trace(
            go.Bar(
                name=category_names.get(col, col),
                y=zone_list,
                x=plot_df[col].tolist(),
                orientation="h",
                marker_color=category_colors.get(col, "#333333"),
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
    title="Electricity Production & Consumption by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "power_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Coverage check: by-zone grand total vs. the system-level ("all zone") total
# for the same categories, computed from the identical source rows.
# ---------------------------------------------------------------------------
print("\nElectricity by-zone balance check:")
for scen in plotted_scenarios:
    zoned_total = zone_tables_by_scenario[scen][active_cols].to_numpy().sum()
    system_total = system_level_totals_by_scenario[scen][active_cols].sum()
    diff = zoned_total - system_total
    status = "OK" if abs(diff) < 1e-6 else "MISMATCH"
    print(
        f"  Scenario {scen}: By-zone total={zoned_total:+.4f} EJ, "
        f"System-level total={system_total:+.4f} EJ, "
        f"Diff={diff:+.6f} EJ  [{status}]"
    )
