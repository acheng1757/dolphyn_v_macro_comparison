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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths, load_annual_nsd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

MWH_TO_EJ = 3.6e-9  # 1 MWh = 3.6e9 J; 1 EJ = 1e18 J

# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Ethanol Demand",
    "Non-Served Demand",
    "DryMill_Existing_Non_CCS",
    "DryMill_CCS_60_RETROFIT",
    "DryMill_CCS_90_RETROFIT",
    "DryMill_CCS_60",
    "DryMill_CCS_90",
    "Bio_Ethanol_CCS_20",
    "Bio_Ethanol_CCS_86",
    "Bio_Ethanol_Non_CCS",
    "Ethylene",
    "Ethanol to Gasoline",
    "Ethanol to Diesel",
    "Ethanol to JetFuel",
    "Ethanol to Gasoline Diesel",
]

category_colors = {
    "Bio_Ethanol_Non_CCS":      "#f0cc6a",
    "Bio_Ethanol_CCS_20":       "#d4a017",
    "Bio_Ethanol_CCS_86":       "#8b6500",
    "DryMill_Existing_Non_CCS": "#f4a86a",
    "DryMill_CCS_60_RETROFIT":  "#c45e20",
    "DryMill_CCS_90_RETROFIT":  "#8b3a0f",
    "DryMill_CCS_60":           "#e8630a",
    "DryMill_CCS_90":           "#7a2e0e",
    "Ethylene":                 "#e8630a",
    "Ethanol to Gasoline":       "royalblue",
    "Ethanol to Diesel":         "forestgreen",
    "Ethanol to JetFuel":        "chocolate",
    "Ethanol to Gasoline Diesel": "limegreen",
    "Ethanol Demand":           "bisque",
    "Non-Served Demand":        "red",
}

label_map = {
    "DryMill_Existing_Non_CCS":  "DryMill_Existing_Non_CCS",
    "DryMill_CCS_60_RETROFIT":   "DryMill_CCS_60_RETROFIT",
    "DryMill_CCS_90_RETROFIT":   "DryMill_CCS_90_RETROFIT",
    "DryMill_CCS_60":            "DryMill_CCS_60",
    "DryMill_CCS_90":            "DryMill_CCS_90",
    "Bio_Ethanol_CCS_20":        "Bio_Ethanol_CCS_20",
    "Bio_Ethanol_CCS_86":        "Bio_Ethanol_CCS_86",
    "Bio_Ethanol_Non_CCS":       "Bio_Ethanol_Non_CCS",
    "Ethylene":                  "Ethylene",
    "Ethanol to Gasoline":       "Eth. Upgrading (Gasoline)",
    "Ethanol to Diesel":         "Eth. Upgrading (Diesel)",
    "Ethanol to JetFuel":        "Eth. Upgrading (JetFuel)",
    "Ethanol to Gasoline Diesel": "Eth. Upgrading (Gasoline+Diesel)",
    "Ethanol Demand":            "Ethanol Demand",
    "Non-Served Demand":         "Non-Served Demand",
}

# ---------------------------------------------------------------------
# MACRO ethanol balance mapping
# ---------------------------------------------------------------------

def map_macro_ethanol_category(row):
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Ethanol production technologies
    if sector == "Ethanol":
        return category

    # Dehydration plants in the Ethylene sector consuming ethanol
    if sector == "Ethylene":
        return "Ethylene"

    # Ethanol demand rows from demand.csv
    if sector == "Demand":
        return "Ethanol Demand"

    return None

# ---------------------------------------------------------------------
# Read MACRO ethanol balance
# ---------------------------------------------------------------------

macro_eth_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_eth_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethanol.csv",
    )

    if not os.path.exists(macro_eth_path):
        print(f"Warning: MACRO ethanol balance file not found: {macro_eth_path}")
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

    macro_eth["Scenario"] = scen_short

    macro_eth["Annual_Flow"] = (
        pd.to_numeric(macro_eth["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_eth["Plot_Category"] = macro_eth.apply(
        map_macro_ethanol_category,
        axis=1,
    )

    macro_eth = macro_eth[macro_eth["Plot_Category"].notna()].copy()
    macro_eth_tables.append(macro_eth)


if macro_eth_tables:
    macro_eth_combined = pd.concat(macro_eth_tables, ignore_index=True)

    macro_combined_data = (
        macro_eth_combined
        .groupby(["Scenario", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )
    print(macro_combined_data)
else:
    macro_combined_data = pd.DataFrame(index=scenario_names)


# ---------------------------------------------------------------------
# Add Ethanol_to_X ethanol consumption split by process
# ---------------------------------------------------------------------
# Ethanol_to_X assets are tagged as "Transmission" in Step 1, so they
# are absent from the Ethanol balance file.  We pull their
# ethanol_consumption_edge annual flows (already negative) directly from
# the all_nonzero file, one category per process.

_ETHANOL_UPGRADING_ASSETS = [
    ("Ethanol to Gasoline",       "_Ethanol_to_Gasoline_",       None),
    ("Ethanol to Gasoline Diesel", "_Ethanol_to_Gasoline_Diesel_", None),
    ("Ethanol to Diesel JetFuel", "_Ethanol_to_Diesel_JetFuel_", None),
    ("Ethanol to Diesel",         "_Ethanol_to_Diesel_",         "_Ethanol_to_Diesel_JetFuel_"),
    ("Ethanol to JetFuel",        "_Ethanol_to_JetFuel_",        None),
]


def _load_ethanol_upgrading_consumption(results_dir):
    """Return {plot_category: annual_ethanol_consumption_MWh} for each Ethanol_to_X process."""
    path = os.path.join(
        results_dir,
        "annual_flow_results",
        "all_nonzero_annual_flows_with_categories.csv",
    )
    result = {cat: 0.0 for cat, _, _ in _ETHANOL_UPGRADING_ASSETS}
    if not os.path.exists(path):
        return result
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    if "Edge" not in df.columns or "Annual_Flow" not in df.columns:
        return result
    flows = pd.to_numeric(df["Annual_Flow"], errors="coerce").fillna(0.0)
    for cat, include, exclude in _ETHANOL_UPGRADING_ASSETS:
        mask = (
            df["Edge"].str.contains(include, na=False) &
            df["Edge"].str.endswith("_ethanol_consumption_edge")
        )
        if exclude is not None:
            mask &= ~df["Edge"].str.contains(exclude, na=False)
        result[cat] = flows[mask].sum()
    return result


for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    process_flows = _load_ethanol_upgrading_consumption(results_dir)
    for cat, raw_flow in process_flows.items():
        if cat not in macro_combined_data.columns:
            macro_combined_data[cat] = 0.0
        if scen_short in macro_combined_data.index:
            macro_combined_data.loc[scen_short, cat] = raw_flow * MWH_TO_EJ


# ---------------------------------------------------------------------
# Align columns
# ---------------------------------------------------------------------

for col in desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

for scen_short, scen_path in macro_scenario_paths.items():
    if scen_short in macro_combined_data.index:
        nsd = load_annual_nsd(scen_path, "ethanol_demand_") * MWH_TO_EJ
        macro_combined_data.loc[scen_short, "Non-Served Demand"] = nsd

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [desired_order]
)

print("\nMACRO ethanol balance by scenario (EJ):")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Ethanol balance check:")
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
# Plot
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

# Only keep columns with non-zero values, preserving desired_order
    # 1 noise threshold
active_cols = [col for col in desired_order if plot_df[col].abs().sum() > 1e-6]
plot_df = plot_df[active_cols]

fig, ax = plt.subplots(figsize=(5.2, 3.2))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in active_cols],
)

ax.set_yticklabels(scenario_names, fontsize=14)
ax.set_ylabel("")
ax.set_title("Ethanol Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
ax.invert_yaxis()

handles, labels = ax.get_legend_handles_labels()
label_to_handle = dict(zip(labels, handles))

# Only include active_cols that actually got plotted
custom_handles = [label_to_handle[col] for col in active_cols if col in label_to_handle]
custom_labels  = [label_map[col]       for col in active_cols if col in label_to_handle]

ax.legend(
    custom_handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.30),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.40)
plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------

fig_plotly = go.Figure()
for col in active_cols:
    fig_plotly.add_trace(go.Bar(
        name=label_map.get(col, col),
        y=scenario_names,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=category_colors.get(col, '#333333'),
        hovertemplate='%{fullData.name}: %{x:.4f} EJ<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Ethanol Balance (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ethanol_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')
