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

# flows.csv already has signs for consumption and production
# (-) means consumption pointing towards the asset
# (+) means production pointing away from the asset

# If there is both consumption AND production, then it will show as a net total in the plot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

# MACRO annual_flow values are treated as MWh, consistent with previous plots.
MWH_TO_EJ = 3.6e-9

# ---------------------------------------------------------------------
# Plot categories
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
# MACRO NG balance mapping
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


# ---------------------------------------------------------------------
# Read MACRO NG balance from annual_flows_balance_NG.csv
# ---------------------------------------------------------------------

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
# Check table
# ---------------------------------------------------------------------

print("\nMACRO NG balance by scenario (EJ):")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Natural Gas balance check:")
for scen in macro_combined_data.index:
    row = macro_combined_data.loc[scen]
    total_positive = row[row > 0].sum()
    total_negative = row[row < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} EJ, "
        f"Demand={total_negative:+.4f} EJ, "
        f"Net={net:+.4f} EJ  [{status}]"
    )

# ---------------------------------------------------------------------
# Plot MACRO-only NG balance
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

fig, ax = plt.subplots(figsize=(5.0, 3.0))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)

ax.set_ylabel("")
ax.set_title("NG Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-12, 12)
ax.set_xticks([-10, -5, 0, 5, 10])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

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

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.36)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------

fig_plotly = go.Figure()

for col in desired_order:
    display_name = category_names.get(col, col)
    color = category_colors.get(col, '#333333')
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=scenario_names,
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

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ng_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')