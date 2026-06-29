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
# Desired order, colors, and labels (same as H2_Macro.py, minus
# Non-Served Demand, which has no per-zone breakdown in this dataset)
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Synthetic FT",
    "Synthetic NG",
    "Ethylene Sector",
    "Ethanol Upgrading",
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
    "Ethylene Sector": "#e8630a",
    "Ethanol Upgrading": "#d4a017",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Ethylene Sector": "Ethylene Sector",
    "Ethanol Upgrading": "Ethanol Upgrading",
    "Demand": "Demand",
}

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name.

    Production/consumption edges put the zone first:
        CA_Electrolyzer_h2_edge
        Existing_CEN_F-NGin-H2out_h2_production_edge
        CEN_Ethanol_to_Diesel_h2_consumption_edge

    Demand-sector edges put the zone last:
        Hydrogen_MW_NE

    Global/system-wide edges (e.g. Ethylene's global demand row feeding
    into the Ethylene Sector category) have no zone and return None.
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
# MACRO H2 balance mapping (same as H2_Macro.py)
# ---------------------------------------------------------------------

def map_macro_h2_category(row):
    """
    Map MACRO annual_flows_balance_H2.csv rows to H2-balance
    plotting categories.
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
        return "Ethylene Sector"

    if sector == "Ethanol Upgrading":
        return "Ethanol Upgrading"

    return None


# ---------------------------------------------------------------------
# Read MACRO H2 balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
system_level_totals_by_scenario = {}

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

    # System-level total: the same aggregate H2_Macro.py would show, used
    # as the "all zone" reference for the coverage check below.
    system_level_totals_by_scenario[scen_short] = (
        macro_h2.groupby("Plot_Category")["Annual_Flow"].sum()
        .reindex(desired_order)
        .fillna(0.0)
    )

    macro_h2["Zone"] = macro_h2["Edge"].apply(extract_zone)
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

    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nH2 production/consumption by zone — Scenario {scen_short} (EJ):")
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
    title="H2 Production & Consumption by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "h2_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Coverage check: by-zone grand total vs. the system-level ("all zone") total
# for the same categories, computed from the identical source rows. A
# mismatch means some rows didn't get a zone assigned and were dropped.
# ---------------------------------------------------------------------------
print("\nH2 by-zone balance check:")
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
