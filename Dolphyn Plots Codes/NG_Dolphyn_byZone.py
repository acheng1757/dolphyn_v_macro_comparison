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
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

file_paths = [f'{dolphyn_base_dir}/ethylene_only_test/{dolphyn_results_folder}/Results_NG/NG_Balance.csv']

conversion_factor = 0.293071 * 3.6e-9  # MWh -> EJ

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
# z1..z9 in Network.csv = CA, NW, SW, TX, NCEN, CEN, SE, MIDAT, NE — same
# zone order used by the ethylene by-zone plots.
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def _zone_name(zone_num):
    return zone_list[int(zone_num) - 1]


# ---------------------------------------------------------------------
# Desired order, colors, and labels (same styling as NG_Dolphyn.py)
# ---------------------------------------------------------------------

columns_of_interest = [
    "Syn_NG", "Bio_NG", "Conventional_NG", "NG_Demand", "Power", "H2",
    "CSC", "BESC", "Ethylene Consumption", "Ethylene Production",
]

category_colors = {
    "Syn_NG": "violet",
    "Bio_NG": "seagreen",
    "Conventional_NG": "lightgrey",
    "NG_Demand": "bisque",
    "Power": "orange",
    "H2": "deepskyblue",
    "CSC": "darkblue",
    "BESC": "mediumseagreen",
    "Ethylene Production": "red",
    "Ethylene Consumption": "darkred",
}

category_names = {
    "Syn_NG": "Syn. NG",
    "Bio_NG": "Bio NG Prod.",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC",
    "BESC": "Bio NG Prod.",
    "Ethylene Consumption": "Ethylene (Consumption)",
    "Ethylene Production": "Ethylene (Production)",
}

desired_order = [
    "NG_Demand",
    "Power",
    "H2",
    "CSC",
    "BESC",
    "Ethylene Production",
    "Ethylene Consumption",
    "Syn_NG",
    "Bio_NG",
    "Conventional_NG",
]


# ---------------------------------------------------------------------
# Load NG_Balance.csv, keeping each (Resource, Zone) pair as its own row
# instead of summing across zones.
# ---------------------------------------------------------------------

def load_ng_balance_by_zone(path, scenario):
    df_raw = pd.read_csv(path, index_col=0)
    df_raw.index = df_raw.index.astype(str).str.strip()

    zone_row = pd.to_numeric(df_raw.loc["Zone"], errors="coerce")
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    # Resource columns repeat per zone with pandas' auto-dedup suffix (.1, .2, …)
    base_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                  for col in df_raw.columns]

    df = pd.DataFrame({
        "Resource": base_names,
        "Zone": zone_row.values,
        "Value": annual_row.values * conversion_factor,
    })
    df = df[df["Zone"].notna()].copy()
    df["Zone"] = df["Zone"].apply(_zone_name)
    df = df[df["Resource"].isin(columns_of_interest)].copy()

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


# ---------------------------------------------------------------------
# Main loading loop
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}

for path, scen_short in zip(file_paths, scenario_names):
    if not os.path.exists(path):
        print(f"Warning: NG_Balance.csv not found: {path}")
        continue

    zone_table = load_ng_balance_by_zone(path, scen_short)
    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nNG balance by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Balance check: zoned + categorized total vs. the file's own AnnualSum
# row total (these won't match exactly since NG_Pipeline isn't a plotted
# category — same comparison NG_Dolphyn.py already prints).
# ---------------------------------------------------------------------
print("\nNG by-zone balance check:")
for path, scen_short in zip(file_paths, scenario_names):
    if scen_short not in zone_tables_by_scenario:
        continue

    df_raw = pd.read_csv(path, index_col=0)
    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)
    file_total = annual_row.sum() * conversion_factor

    zoned_total = zone_tables_by_scenario[scen_short].to_numpy().sum()
    print(
        f"  {scen_short}: file AnnualSum total = {file_total:+.4f} EJ, "
        f"zoned+categorized total = {zoned_total:+.4f} EJ"
    )


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
    title="NG Balance by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ng_byzone_dolphyn_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")
