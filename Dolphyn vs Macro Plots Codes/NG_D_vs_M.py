#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

dolphyn_scenario_paths = {
    "1": f'all_demand_test/{dolphyn_results_folder}',
}

macro_scenario_paths = {
    "1": f"6_15_168_restart_all_demand/results_001/results",
}

# Dolphyn NG_Balance values are treated as MMBtu.
MMBTU_TO_EJ = 0.293071 * 3.6e-9

# MACRO annual_flow values are treated as MWh, consistent with previous plots.
MWH_TO_EJ = 3.6e-9

# ---------------------------------------------------------------------
# Plot categories
# ---------------------------------------------------------------------

# Dolphyn columns of interest
columns_of_interest = ["Syn_NG", "Bio_NG", "Conventional_NG", "NG_Demand", "Power", "H2", "CSC", "BESC", "Ethylene"]

# Desired plotting order
desired_order = [
    "NG_Demand",
    "Ethylene",
    "Power",
    "H2",
    "CSC",
    "BESC",
    "Syn_NG",
    "Bio_NG",
    "Conventional_NG",
    "Ethanol"
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
    "Ethylene": "lightsalmon",
    "Ethanol": "lightsalmon",
}

# this only replaces the legend labels
category_names = {
    "Syn_NG": "Syn. NG",
    "Bio_NG": "Bio NG",
    "Conventional_NG": "Fossil NG",
    "NG_Demand": "Demand",
    "Power": "Power Sector",
    "H2": "H2 Sector",
    "CSC": "Solvent DAC",
    "BESC": "Bio NG Prod.",
    "Ethylene": "Ethylene",
    "Ethanol": "Ethanol",
}

# ---------------------------------------------------------------------
# Dolphyn NG balance
# ---------------------------------------------------------------------

global_values_per_scenario = {}

for scenario, scen_folder in dolphyn_scenario_paths.items():
    path = os.path.join(
        dolphyn_base_dir,
        scen_folder,
        "Results_NG/NG_Balance.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dolphyn NG balance file not found: {path}")

    df = pd.read_csv(path, header=0)
    df.columns = df.columns.str.strip()

    annual_sum_row = df[df.iloc[:, 0] == "AnnualSum"]

    if not annual_sum_row.empty:
        global_values = {}

        for col in columns_of_interest:
            col_values = (
                annual_sum_row
                .filter(like=col, axis=1)
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0.0)
                .sum(axis=1)
                .values
                * MMBTU_TO_EJ
            )

            global_values[col] = col_values[0] if col_values.size > 0 else 0.0

    else:
        global_values = {col: 0.0 for col in columns_of_interest}

    global_values_per_scenario[scenario] = global_values

dolphyn_combined_data = pd.DataFrame(global_values_per_scenario).T
dolphyn_combined_data = dolphyn_combined_data.reindex(scenario_names).fillna(0.0)

for col in desired_order:
    if col not in dolphyn_combined_data.columns:
        dolphyn_combined_data[col] = 0.0

dolphyn_combined_data = dolphyn_combined_data[desired_order]


# ---------------------------------------------------------------------
# MACRO NG balance from annual_flows_balance_NG.csv
# ---------------------------------------------------------------------

def map_macro_ng_category(row):
    """
    Map MACRO annual_flows_balance_NG.csv rows to the same NG balance
    categories used for Dolphyn.

    In annual_flows_balance_NG.csv:
      - demand is Category = NG End Use
      - fossil purchase is Category = NG Fossil Upstream
    """

    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # NG demand from demand.csv
    if sector == "Demand":
        return "NG_Demand"

    # NG demand / end use
    #if category == "NG End Use":
    #    return "NG_Demand"

    # Fossil / conventional NG purchase
    if category == "NG Fossil Upstream":
        return "Conventional_NG"

    # Synthetic NG supply
    if sector == "Synthetic fuels" and category == "S-NG":
        return "Syn_NG"

    # Power-sector NG consumption
    if sector == "Power":
        return "Power"

    # H2-sector NG consumption
    if sector == "Hydrogen":
        return "H2"

    # CO2-sector NG consumption
    if sector == "CO2":
        return "CSC"

    # Bioenergy-sector NG flows
    if sector == "Bioenergy":
        return "BESC"

    if sector == "Ethylene":
        return "Ethylene"

    if sector == "Ethanol":
        return "Ethanol"

    return None


macro_ng_tables = []

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

    macro_ng["Scenario"] = scen_short
    macro_ng["Annual_Flow"] = (
        pd.to_numeric(macro_ng["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_ng["Plot_Category"] = macro_ng.apply(
        map_macro_ng_category,
        axis=1,
    )

    macro_ng = macro_ng[macro_ng["Plot_Category"].notna()].copy()

    macro_ng_tables.append(macro_ng)

if macro_ng_tables:
    macro_ng_combined = pd.concat(macro_ng_tables, ignore_index=True)

    macro_combined_data = (
        macro_ng_combined
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
# Optional checks
# ---------------------------------------------------------------------

print("\nDolphyn NG balance by scenario (EJ):")
print(dolphyn_combined_data)

print("\nMACRO NG balance by scenario (EJ):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Build paired plotting table
# ---------------------------------------------------------------------

plot_rows = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(dolphyn_combined_data.loc[scen, desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, desired_order])
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
# Print net NG balance (production + and consumption -) before plotting
# ---------------------------------------------------------------------

print("\nNG Net Balance Summary (EJ):")
print(f"{'Scenario':<20} {'Model':<10} {'Production (+)':<18} {'Consumption (-)':<18} {'Net Balance':<12}")
print("-" * 80)
for (scen, model), row in plot_df.iterrows():
    production = row[row > 0].sum()
    consumption = row[row < 0].sum()
    net = production + consumption
    print(f"{scen:<20} {model:<10} {production:<18.4f} {consumption:<18.4f} {net:<12.4f}")

# ---------------------------------------------------------------------
# Plot Dolphyn and MACRO NG balance side by side
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
    color=[category_colors[col] for col in desired_order],
)

# Move bars from default positions 0, 1, 2, ... to custom positions with gaps
for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("NG Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-12, 12)
ax.set_xticks([-10, -5, 0, 5, 10])
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
custom_labels = [category_names[col] for col in desired_order]

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

for col in desired_order:
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
    title='NG Balance (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ng_d_vs_m_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')