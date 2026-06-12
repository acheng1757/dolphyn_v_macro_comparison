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
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

# MACRO captured CO2 values are treated as tonnes CO2.
TONNE_TO_MT = 1e-6


# ---------------------------------------------------------------------
# Plot categories
# ---------------------------------------------------------------------

desired_order = [
    "CO2 Storage",
    "Synthetic Fuels",
    "Synthetic NG",
    "NG Power CCS",
    "NG H2 CCS",
    "Ethylene CCS",
    "Ethanol CCS",
    "DAC Capture",
    "Biomass Capture",
]

category_colors = {
    "Biomass Capture": "olivedrab",
    "DAC Capture": "darkblue",
    "NG Power CCS": "orange",
    "NG H2 CCS": "deepskyblue",
    "Synthetic Fuels": "purple",
    "Synthetic NG": "#e8905a",
    "Ethylene CCS": "#e8630a",
    "Ethanol CCS": "#d4a017",
    "CO2 Storage": "darkgoldenrod",
}

category_names = {
    "CO2 Storage": "CO2 Storage",
    "Synthetic NG": "Syn. NG",
    "Synthetic Fuels": "Syn. Liquids",
    "NG Power CCS": "Power CCS",
    "NG H2 CCS": "H2 CCS",
    "Ethylene CCS": "Ethylene CCS",
    "Ethanol CCS": "Ethanol CCS",
    "DAC Capture": "DAC",
    "Biomass Capture": "BECCS",
}


# ---------------------------------------------------------------------
# MACRO captured CO2 balance mapping
# ---------------------------------------------------------------------

def map_macro_captured_co2_category(row):
    """
    Map MACRO captured CO2 balance rows to plotting categories.

    MACRO is grouped by Sector, except Synthetic fuels:
      - if Edge contains Syn_NG, assign to Synthetic NG
      - otherwise assign to Synthetic Fuels
    """
    sector = str(row.get("Sector", "")).strip()
    edge = str(row.get("Edge", "")).strip()

    edge_lower = edge.lower()

    if sector == "CO2 Storage":
        return "CO2 Storage"

    if sector == "CO2":
        return "DAC Capture"

    if sector == "Bioenergy":
        return "Biomass Capture"

    if sector == "Power":
        return "NG Power CCS"

    if sector == "Hydrogen":
        return "NG H2 CCS"

    if sector == "Synthetic fuels":
        if "syn_ng" in edge_lower:
            return "Synthetic NG"

        return "Synthetic Fuels"

    if sector == "Ethylene":
        return "Ethylene CCS"

    if sector == "Ethanol":
        return "Ethanol CCS"

    return None


# ---------------------------------------------------------------------
# Read MACRO captured CO2 balance
# ---------------------------------------------------------------------

macro_tables = []

for scen_short, scen_path in macro_scenario_paths.items():

    candidate_paths = [
        os.path.join(
            macro_base_dir,
            scen_path,
            "annual_flow_results",
            "balance_specific_flows",
            "annual_flows_balance_Captured_CO2.csv",
        ),
        os.path.join(
            macro_base_dir,
            scen_path,
            "annual_flow_results",
            "balance_specific_flows",
            "annual_flows_balance_CO2.csv",
        ),
    ]

    macro_path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if macro_path is None:
        print(
            "Warning: MACRO captured CO2 balance file not found for "
            f"{scen_short}. Checked:\n  " + "\n  ".join(candidate_paths)
        )
        continue

    macro_df = pd.read_csv(macro_path)
    macro_df.columns = macro_df.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_df.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_df.columns.tolist()}"
        )

    macro_df["Scenario"] = scen_short

    macro_df["Annual_Flow"] = (
        pd.to_numeric(macro_df["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * TONNE_TO_MT
    )

    macro_df["Plot_Category"] = macro_df.apply(
        map_macro_captured_co2_category,
        axis=1,
    )

    macro_df = macro_df[macro_df["Plot_Category"].notna()].copy()

    macro_tables.append(macro_df)


if macro_tables:
    macro_combined = pd.concat(macro_tables, ignore_index=True)

    macro_combined_data = (
        macro_combined
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

print("\nMACRO captured CO2 balance by scenario (Mt):")
print(macro_combined_data)

print("\nMACRO net captured CO2 balance by scenario (Mt):")
print(macro_combined_data.sum(axis=1))

print("CO2 Capture balance check:")
for scen in macro_combined_data.index:
    row = macro_combined_data.loc[scen]
    total_positive = row[row > 0].sum()
    total_negative = row[row < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} Mt, "
        f"Demand={total_negative:+.4f} Mt, "
        f"Net={net:+.4f} Mt  [{status}]"
    )


# ---------------------------------------------------------------------
# Plot MACRO-only captured CO2 balance
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
ax.set_title("Captured CO2 Balance (Mt)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

_pos_ext = plot_df.clip(lower=0).sum(axis=1).max()
_neg_ext = plot_df.clip(upper=0).sum(axis=1).min()
_pad = max(abs(_pos_ext), abs(_neg_ext)) * 0.12 or 1.0
ax.set_xlim(_neg_ext - _pad, _pos_ext + _pad)
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

'''
# Optional target storage indicators
indicator_height = 0.18
target_values = {
    "HB-HS": -865.8,
    "HB-LS": -433.8,
    "LB-HS": -865.8,
    "LB-LS": -433.8,
}

for i, scen in enumerate(scenario_names):
    target_value = target_values.get(scen, None)

    if target_value is not None:
        ax.barh(
            i,
            20,
            height=indicator_height,
            color="black",
            alpha=0.8,
            left=target_value,
        )
'''

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

_active_cols = [col for col in desired_order if plot_df[col].abs().sum() > 0]

fig_plotly = go.Figure()
for col in _active_cols:
    fig_plotly.add_trace(go.Bar(
        name=category_names.get(col, col),
        y=scenario_names,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=category_colors.get(col, '#333333'),
        hovertemplate='%{fullData.name}: %{x:.2f} Mt<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Captured CO2 Balance (Mt)',
    xaxis_title='Mt',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_capture_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')