#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths, macro_input_paths, load_annual_nsd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Ethylene Demand",
    "Non-Served Demand",
    "Existing TSC:H2",
    "Ret-TSC:H2",
    "Ret-TSC",
    "Ret-TSC+CC90",
    "Ret-TSC+CC90:H2",
    "Ret-TSC+H2in",
    "Ret-TSC+CC90+H2in",
    "Ret-ESC",
    "Ret-TSC+H2in:CH4",

    "TSC:H2",   
    "TSC",
    "TSC+CC90",
    "TSC+CC90:H2",
    "TSC+H2in",
    "TSC+CC90+H2in",
    "TSC+H2in:CH4",

    "ESC",

    "Existing Capacities",
    "MS+MTO",

    "MS+MTO+CC90",
    "Dehydration NGfuel",
    "Dehydration H2fuel",
]

category_colors = {
    "TSC":                  "#e8630a",
    "Ret-TSC":              "#e8630a",   # same as TSC

    "TSC+CC90":             "#7a2e0e",
    "Ret-TSC+CC90":         "#7a2e0e",   # same as TSC+CC90

    "TSC:H2":               "#f5c518",
    "Ret-TSC:H2":           "#f5c518",   # same as TSC:H2
    "Existing TSC:H2":      "#f5c518",   # same as TSC:H2

    "MS+MTO":               "#9b59b6",
    "MS+MTO+CC90":          "#4a1a6e",

    "TSC+CC90:H2":          "#a07c00",
    "Ret-TSC+CC90:H2":      "#a07c00",   # same as TSC+CC90:H2

    "TSC+H2in":             "#3a8fd1",
    "Ret-TSC+H2in":         "#3a8fd1",   # same as TSC+H2in

    "TSC+H2in:CH4":         "#1a4f80",
    "Ret-TSC+H2in:CH4":     "#1a4f80",   # same as TSC+H2in:CH4

    "TSC+CC90+H2in":        "midnightblue",
    "Ret-TSC+CC90+H2in":    "midnightblue",   # same as TSC+CC90+H2in

    "Existing Capacities":  "#f5c518",   # same as TSC:H2 (existing thermal crackers)
    "ESC":                  "#808080",
    "Ret-ESC":              "#808080",   # same as ESC

    "Dehydration NGfuel":   "#57c46a",
    "Dehydration H2fuel":   "#1a6e30",
    "Ethylene Demand":      "bisque",
    "Non-Served Demand":    "red",
}

# Pattern encodes build type: "" = new build, "//" = retrofit (Ret-), ".." = existing
category_hatch = {
    "TSC":                  "",
    "Ret-TSC":              "//",
    "TSC+CC90":             "",
    "Ret-TSC+CC90":         "//",
    "TSC:H2":               "",
    "Ret-TSC:H2":           "//",
    "Existing TSC:H2":      "..",
    "MS+MTO":               "",
    "MS+MTO+CC90":          "",
    "TSC+CC90:H2":          "",
    "Ret-TSC+CC90:H2":      "//",
    "TSC+H2in":             "",
    "Ret-TSC+H2in":         "//",
    "TSC+H2in:CH4":         "",
    "Ret-TSC+H2in:CH4":     "//",
    "TSC+CC90+H2in":        "",
    "Ret-TSC+CC90+H2in":    "//",
    "Existing Capacities":  "..",
    "ESC":                  "",
    "Ret-ESC":              "//",
    "Dehydration NGfuel":   "",
    "Dehydration H2fuel":   "",
    "Ethylene Demand":      "",
    "Non-Served Demand":    "",
}

label_map = {
    "TSC":                  "TSC",
    "Ret-TSC":              "Ret-TSC",

    "TSC+CC90":             "TSC+CC90",
    "Ret-TSC+CC90":         "Ret-TSC+CC90",

    "TSC:H2":               "TSC:H2",
    "Ret-TSC:H2":          "Ret-TSC:H2",
    "Existing TSC:H2":  "Existing TSC:H2",

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
    "Non-Served Demand":    "Non-Served Demand",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC", # confirm grouping
}

# ---------------------------------------------------------------------
# MACRO ethylene balance mapping
# ---------------------------------------------------------------------
'''
def map_macro_ethylene_category(row):
    """
    Map MACRO annual_flows_balance_Ethylene.csv rows to plot categories.

    Production (positive Annual_Flow):
        Thermal Steam Cracker  → F-* assets excluding F-Ein
        Electric Steam Cracker → F-Ein
        Ethanol Dehydration    → B-* assets
        Synthetic Ethylene     → S-* assets

    Consumption (negative Annual_Flow):
        Ethylene Demand        → Demand sector rows
    """
    sector   = str(row.get("Sector",   "")).strip()
    category = str(row.get("Category", "")).strip()
    edge     = str(row.get("Edge",     "")).strip()

    sector_lower   = sector.lower()
    category_lower = category.lower()
    edge_lower     = edge.lower()

    # ------------------------------------------------------------------
    # Demand rows
    # ------------------------------------------------------------------
    if sector_lower == "demand":
        return "Ethylene Demand"

    # ------------------------------------------------------------------
    # Ethylene sector — map by category (set in sector_definitions)
    # ------------------------------------------------------------------
    if sector_lower == "ethylene":
        if category == "Electric Steam Cracker":
            return "Electric Steam Cracker"

        if category == "Thermal Steam Cracker":
            return "Thermal Steam Cracker"

        if category == "Ethanol Dehydration":
            return "Ethanol Dehydration"

        if category == "Synthetic Ethylene":
            return "Synthetic Ethylene"

    # ------------------------------------------------------------------
    # Fallback: try to infer directly from the edge name in case
    # sector/category tagging is incomplete
    # ------------------------------------------------------------------
    if "f-ein" in edge_lower:
        return "Electric Steam Cracker"

    if any(x in edge_lower for x in ["f-ngin", "f-cc90", "f-h2in", "f-ngin-h2out",
                                       "f-cc90-ngin", "f-cc90-ngin-h2out",
                                       "f-h2in-ch4out"]):
        return "Thermal Steam Cracker"

    if any(x in edge_lower for x in ["b-ngin", "b-h2in"]):
        return "Ethanol Dehydration"

    if any(x in edge_lower for x in ["s-h2in", "s-cc90-h2in"]):
        return "Synthetic Ethylene"

    return None

def map_macro_ethylene_category(row):
    sector   = str(row.get("Sector",   "")).strip()
    category = str(row.get("Category", "")).strip()

    if sector.lower() == "demand":
        return "Ethylene Demand"

    mapping = {
        "Thermal SC NGfuel":            "Thermal SC NGfuel",
        "Thermal SC CC90 NGfuel":       "Thermal SC CC90 NGfuel",
        "Thermal SC NGfuel H2out":      "Thermal SC NGfuel H2out",
        "Thermal SC CC90 NGfuel H2out": "Thermal SC CC90 NGfuel H2out",
        "Thermal SC H2fuel":            "Thermal SC H2fuel",
        "Thermal SC H2fuel CH4out":     "Thermal SC H2fuel CH4out",
        "Electric SC":                  "Electric SC",
        "Dehydration NGfuel":           "Dehydration NGfuel",
        "Dehydration H2fuel":           "Dehydration H2fuel",
        "Synthetic H2fuel":             "Synthetic H2fuel",
        "Synthetic CC90 H2fuel":        "Synthetic CC90 H2fuel",
    }

    return mapping.get(category, None)
'''

# ---------------------------------------------------------------------
# Read MACRO ethylene balance
# ---------------------------------------------------------------------

macro_eth_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_eth_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethylene.csv",
    )

    if not os.path.exists(macro_eth_path):
        print(f"Warning: MACRO ethylene balance file not found: {macro_eth_path}")
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
    )

    macro_eth["Plot_Category"] = macro_eth["Category"]

    '''
    macro_eth["Plot_Category"] = macro_eth.apply(
        map_macro_ethylene_category,
        axis=1,
    )
    '''

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
# Align columns
# ---------------------------------------------------------------------

for col in desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

for scen_short, scen_path in macro_scenario_paths.items():
    if scen_short in macro_combined_data.index:
        # NSD file values are in the same raw units as Annual_Flow (no conversion)
        nsd = load_annual_nsd(scen_path, "ethylene_demand_")
        macro_combined_data.loc[scen_short, "Non-Served Demand"] = nsd

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [desired_order]
)

print("\nMACRO ethylene balance by scenario (tonnes):")
print(macro_combined_data)

# Existing steam cracker capacity is one shared physical-infrastructure
# fact, not scenario-specific — but not every scenario variant ships its
# own existing_steam_crackers.json, so try each plotted scenario in turn
# and use the first one that actually has the data, rather than failing
# the reference line for the whole chart just because scenario_names[0]
# happens to lack it.
_t_ethane_p_t_ethylene = 1.4277269  # t-ethane/t-ethylene
_mwh_ethane_p_t_ethane = 14.41666667      # MWh-ethane/t-ethane (LHV)

existing_cracker_cap = None
for _scen in scenario_names:
    _crackers_json_path = os.path.join(
        macro_base_dir,
        macro_input_paths[_scen],
        "assets",
        "existing_steam_crackers.json",
    )
    try:
        with open(_crackers_json_path) as _f:
            _crackers = json.load(_f)

        _total_cap_mwh_per_hr = sum(
            inst["edges"]["ethane_consumption_edge"]["existing_capacity"]
            for asset in _crackers["steamcracker_existing"]
            for inst in asset["instance_data"]
        )

        print(f"_total_cap_mwh_per_hr: {_total_cap_mwh_per_hr}")
        print(f"_mwh_ethane_p_t_ethane: {_mwh_ethane_p_t_ethane}")
        print(f"_t_ethane_p_t_ethylene: {_t_ethane_p_t_ethylene}")

        # MWh-ethane/hr ÷ (MWh/t-ethane) ÷ (t-ethane/t-ethylene) × 8760 hr/yr → t-ethylene/yr
        existing_cracker_cap = (
            _total_cap_mwh_per_hr / _mwh_ethane_p_t_ethane / _t_ethane_p_t_ethylene * 8760
        )
        break
    except Exception as exc:
        print(f"Warning: could not load existing steam cracker capacity for {_scen} "
              f"from {_crackers_json_path}: {exc}")

if existing_cracker_cap is None:
    print("Warning: no scenario had usable existing steam cracker capacity data; omitting reference lines.")


# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Ethylene balance check:")
for scen in macro_combined_data.index:
    row = macro_combined_data.loc[scen]
    total_positive = row[row > 0].sum()
    total_negative = row[row < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} tonnes, "
        f"Demand={total_negative:+.4f} tonnes, "
        f"Net={net:+.4f} tonnes  [{status}]"
    )


# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

# Only keep columns with non-zero values, preserving desired_order
    # 1 noise threshold
active_cols = [col for col in desired_order if plot_df[col].abs().sum() > 1.0]
plot_df = plot_df[active_cols]

fig, ax = plt.subplots(figsize=(5.2, 3.2))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in active_cols],
)

for container, col in zip(ax.containers, active_cols):
    hatch = category_hatch.get(col, "")
    for patch in container.patches:
        patch.set_hatch(hatch)
        patch.set_edgecolor("white" if hatch else "none")

ax.set_yticklabels(scenario_names, fontsize=14)
ax.set_ylabel("")
ax.set_title("Ethylene Balance (tonnes)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
if existing_cracker_cap is not None:
    ax.axvline(x=existing_cracker_cap, color="red", linewidth=1.5, linestyle="--",
               label="Total Existing Capacity")
    ax.axvline(x=0.8 * existing_cracker_cap, color="red", linewidth=1, linestyle=":",
               label="80% Existing Capacity")
ax.invert_yaxis()

handles, labels = ax.get_legend_handles_labels()
label_to_handle = dict(zip(labels, handles))

# Only include active_cols that actually got plotted, plus the capacity lines
custom_handles = [label_to_handle[col] for col in active_cols if col in label_to_handle]
custom_labels  = [label_map[col]       for col in active_cols if col in label_to_handle]
if "Total Existing Capacity" in label_to_handle:
    custom_handles.append(label_to_handle["Total Existing Capacity"])
    custom_labels.append("Total Existing Capacity")
if "80% Existing Capacity" in label_to_handle:
    custom_handles.append(label_to_handle["80% Existing Capacity"])
    custom_labels.append("80% Existing Capacity")

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

_plotly_hatch_map = {"//": "/", "..": "."}

fig_plotly = go.Figure()

for col in active_cols:
    display_name = label_map.get(col, col)
    color = category_colors.get(col, '#333333')
    pattern_shape = _plotly_hatch_map.get(category_hatch.get(col, ""), "")
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=scenario_names,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=color,
        marker_pattern_shape=pattern_shape,
        marker_pattern_fgcolor="white",
        marker_pattern_fillmode="overlay",
        hovertemplate='%{fullData.name}: %{x:.2f} tonnes<extra></extra>',
    ))

_capacity_shapes = []
_capacity_annotations = []
if existing_cracker_cap is not None:
    _capacity_shapes = [
        dict(type='line', x0=existing_cracker_cap, x1=existing_cracker_cap,
             y0=-0.5, y1=len(plot_df) - 0.5, yref='y',
             line=dict(color='red', width=1.5, dash='dash')),
        dict(type='line', x0=0.8 * existing_cracker_cap, x1=0.8 * existing_cracker_cap,
             y0=-0.5, y1=len(plot_df) - 0.5, yref='y',
             line=dict(color='red', width=1, dash='dot')),
    ]
    _capacity_annotations = [
        dict(x=existing_cracker_cap, y=len(plot_df) - 0.5,
             xref='x', yref='y', yanchor='bottom',
             text='Total Existing Capacity', showarrow=False,
             font=dict(color='red', size=11)),
        dict(x=0.8 * existing_cracker_cap, y=len(plot_df) - 0.5,
             xref='x', yref='y', yanchor='bottom',
             text='80% Existing Capacity', showarrow=False,
             font=dict(color='red', size=11)),
    ]

fig_plotly.update_layout(
    barmode='relative',
    title='Ethylene Balance (tonnes)',
    xaxis_title='tonnes',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[
        dict(type='line', x0=0, x1=0, y0=-0.5,
             y1=len(plot_df) - 0.5, yref='y',
             line=dict(color='black', width=1, dash='dash')),
    ] + _capacity_shapes,
    annotations=_capacity_annotations,
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ethylene_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')
