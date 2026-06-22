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
# Desired order, colors, and labels (same as NG_Macro.py, minus
# Non-Served Demand, which has no per-zone breakdown in this dataset)
# ---------------------------------------------------------------------

desired_order = [
    "NG_Demand",
    "Power",
    "H2",
    "CSC",
    "BESC",
    "Ethylene",
    "Ethanol",
    "Syn_NG",
    "Conventional_NG",
]

category_colors = {
    "Syn_NG": "#e8905a",
    "Conventional_NG": "#c0504d",
    "NG_Demand": "bisque",
    "Power": "orange",
    "H2": "deepskyblue",
    "CSC": "darkblue",
    "BESC": "seagreen",
    "Ethylene": "#e8630a",
    "Ethanol": "#d4a017",
}

category_names = {
    "Syn_NG": "Syn. NG",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC",
    "BESC": "Bio NG",
    "Ethylene": "Ethylene Sector",
    "Ethanol": "Ethanol Sector",
}

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name.

    Production/consumption edges put the zone first:
        CEN_Bio_NG_Herb_natgas_edge
        Existing_CEN_F-NGin-H2out_natgas_consumption_edge
    Demand-sector edges put the zone last:
        NaturalGas_MW_NW

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
# MACRO NG balance mapping (same as NG_Macro.py)
# ---------------------------------------------------------------------

def map_macro_ng_category(row):
    """
    Map MACRO annual_flows_balance_NG.csv rows to NG balance categories.

    In annual_flows_balance_NG.csv:
      - demand is Category = NG End Use
      - fossil purchase is Category = NG Fossil Upstream
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # NG demand from demand.csv (NaturalGas_MW_* rows)
    # Note: sector=NG / category="NG End Use" rows are the same flows — do NOT map
    # them here or demand will be double-counted.
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
        return "Ethylene"

    if sector == "Ethanol":
        return "Ethanol"

    return None


# ---------------------------------------------------------------------
# Read MACRO NG balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
system_level_totals_by_scenario = {}

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

    system_level_totals_by_scenario[scen_short] = (
        macro_ng.groupby("Plot_Category")["Annual_Flow"].sum()
        .reindex(desired_order)
        .fillna(0.0)
    )

    macro_ng["Zone"] = macro_ng["Edge"].apply(extract_zone)
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

    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nNG production/consumption by zone — Scenario {scen_short} (EJ):")
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
    title="NG Production & Consumption by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ng_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Coverage check: by-zone grand total vs. the system-level ("all zone") total
# for the same categories, computed from the identical source rows.
# ---------------------------------------------------------------------------
print("\nNatural Gas by-zone balance check:")
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
