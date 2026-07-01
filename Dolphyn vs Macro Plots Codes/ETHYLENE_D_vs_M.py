#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------
# Fully manual/self-contained: dolphyn_scenario_paths and
# macro_scenario_paths are the source of truth for which scenarios this
# script compares. scenario_names is derived from them directly rather
# than imported from Step_1, so this script doesn't silently break or
# go stale whenever Step_1's shared scenario config changes.

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir,
    dolphyn_results_folder, load_annual_nsd,
)

dolphyn_scenario_paths = {
    "no_crossover": f'ethylene_only_test/{dolphyn_results_folder}/Results_Ethylene',
    "crossover": f'ethylene_only_test/{dolphyn_results_folder}/Results_Ethylene',
}

macro_scenario_paths = {
    "no_crossover": f"7_1_DOLPHYN_B2/results_001/results",
    "crossover": f"7_1_DOLPHYN_B2/results_002/results",
}

scenario_names = list(dolphyn_scenario_paths.keys())

# Ethylene flows are already in tonnes — no conversion needed for either model.


# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Ethylene Demand",
    "Non-Served Demand",
    "Existing TSC:H2",
    "Existing Capacities",
    "TSC:H2",
    "Ret-TSC:H2",
    "Ret-TSC",
    "Ret-TSC+CC90",
    "Ret-TSC+CC90:H2",
    "Ret-TSC+H2in",
    "Ret-TSC+CC90+H2in",
    "Ret-ESC",
    "Ret-TSC+H2in:CH4",
    "TSC+H2in:CH4",

    "TSC",
    "TSC+CC90",
    "TSC+CC90:H2",
    "TSC+H2in",
    "TSC+CC90+H2in",

    "ESC",

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

    "ESC":                  "#808080",
    "Ret-ESC":              "#808080",   # same as ESC

    "Existing Capacities":  "#f5c518",   # same as TSC:H2 (existing thermal crackers)

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
    "ESC":                  "",
    "Ret-ESC":              "//",
    "Existing Capacities":  "..",
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

    "Existing TSC:H2":  "Existing TSC:H2",

    "Dehydration NGfuel":   "Dehydration NGfuel",
    "Dehydration H2fuel":   "Dehydration H2fuel",
    "Ethylene Demand":      "Ethylene Demand",
    "Non-Served Demand":    "Non-Served Demand",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC", # confirm grouping
    "Existing Capacities":  "Existing Capacities",
}

# ---------------------------------------------------------------------
# Dolphyn: load production from Ethylene_capacity.csv
# ---------------------------------------------------------------------

# used to categorize the label directly in the CSV
RESOURCE_CATEGORY_MAP = {
    "TSC":            "TSC",
    "TSC+CC90": "TSC+CC90",
    "TSC:H2":            "TSC:H2", # not sure about this one
    "TSC: H2":            "TSC:H2", # not sure about this one
    "Bio-eth+CC88:NG":            "Dehydration NGfuel",
    "Bio-eth+CC88:H2":            "Dehydration H2fuel",
    "MS+MTO":            "MS+MTO",
    "MS+MTO+CC90":            "MS+MTO+CC90",
    "TSC+CC90:H2":            "TSC+CC90:H2", # mapping based on what Chaitanya said
    "TSC+CC90: H2":            "TSC+CC90:H2", # mapping based on what Chaitanya said
    "TSC+H2in":            "TSC+H2in",
    "TSC+CC90+H2in":            "TSC+H2in:CH4",
    "ESC":            "ESC",
    "Existing Capacities":            "Existing Capacities",
    "TSC+H2in:CH4":         "TSC+H2in:CH4",
    "TSC+H2in: CH4":         "TSC+H2in:CH4",
}

def categorize_ethylene_resource(resource):
    return RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None)

def load_ethylene_production(balance_path, scenario):

    df_raw = pd.read_csv(balance_path, index_col=0)
    df_raw.index = df_raw.index.str.strip()

    annual_row = pd.to_numeric(df_raw.loc["AnnualSum"], errors="coerce").fillna(0.0)

    # Strip zone suffixes and sum across zones for each unique asset
    clean_names = [col.rsplit(".", 1)[0] if col.rsplit(".", 1)[-1].isdigit() else col
                   for col in df_raw.columns]
    annual_row.index = clean_names
    annual_row = annual_row.groupby(level=0).sum()

    df = pd.DataFrame({
        "Resource": annual_row.index,
        "Annual_Ethylene_Production": annual_row.values,
    })

    # Zero out optimiser noise
    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    print(df["Resource"])
    df = df[df["Plot_Category"].notna()].copy()
    df["Scenario"] = scenario

    print("FINAL ETHYLENE PRODUCTION")
    print(df)

    return df[["Scenario", "Plot_Category", "Annual_Ethylene_Production"]]

def load_ethylene_production_retrofit(balance_retrofit_path, scenario):
    """
    Read Ethylene_Retrofit_Balance.csv and return a DataFrame with columns:
        Scenario, Plot_Category, Annual_Ethylene_Production
    Assets with unmapped resource names are dropped.
    Near-zero values (optimiser noise) are zeroed out.
    """
    with open(balance_retrofit_path) as f:
        raw_header = f.readline().strip().split(",")
    resource_names = [col.strip() for col in raw_header[1:]]  # skip index column

    df_raw = pd.read_csv(balance_retrofit_path, header=0, index_col=0)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw.index = df_raw.index.astype(str).str.strip()

    annual_row = df_raw.loc["AnnualSum"]

    df = pd.DataFrame({
        "Resource": resource_names,
        "Annual_Ethylene_Production": pd.to_numeric(annual_row.values, errors="coerce"),
    }).fillna(0.0)

    print("Raw resource names from CSV:")
    print(df["Resource"].tolist())

    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(
        lambda r: "Ret-" + categorize_ethylene_resource(r)
        if categorize_ethylene_resource(r) is not None
        else None
    )

    print("DF FOR RETROFIT")
    print(df)

    df = df[df["Plot_Category"].notna()].copy()

    df["Scenario"] = scenario
    return df[["Scenario", "Plot_Category", "Annual_Ethylene_Production"]]

def load_dolphyn_ethylene_demand(balance_path):
    df = pd.read_csv(balance_path, header=None)
    resource_row = df.iloc[0].tolist()
    annualsum_row = df[df.iloc[:, 0] == "AnnualSum"]

    if annualsum_row.empty:
        print(f"  Warning: no AnnualSum row found in {balance_path}")
        return 0.0

    demand_cols = [
        i for i, v in enumerate(resource_row)
        if "demand" in str(v).strip().lower()
    ]

    if not demand_cols:
        unique_vals = list(dict.fromkeys(
            [str(v).strip() for v in resource_row if str(v) != "nan"]
        ))
        print(f"  Warning: no demand columns found in {balance_path}")
        print(f"  Header values found: {unique_vals}")
        return 0.0

    total_demand = sum(
        pd.to_numeric(annualsum_row.iloc[0, i], errors="coerce")
        for i in demand_cols
    )

    return float(total_demand) if pd.notna(total_demand) else 0.0


# ---------------------------------------------------------------------
# Dolphyn loading loop
# ---------------------------------------------------------------------

dolphyn_production_tables = []
dolphyn_demand_rows = []

for scen_short, scen_path in dolphyn_scenario_paths.items():
    results_dir = os.path.join(dolphyn_base_dir, scen_path)
    balance_path = os.path.join(results_dir, "Ethylene_Balance_newv.csv")
    balance_retrofit_path = os.path.join(results_dir, "Ethylene_Retrofit_Balance_newv.csv")

    if not os.path.exists(balance_path):
        print(f"Warning: Ethylene_Balance_newv.csv not found: {balance_path}")
        continue

    if not os.path.exists(balance_retrofit_path):
        print(f"Warning: Ethylene_Retrofit_Balance_newv.csv not found: {balance_retrofit_path}")
        continue

    prod_df = load_ethylene_production(balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit(balance_retrofit_path, scen_short)
    dolphyn_production_tables.append(prod_df)
    dolphyn_production_tables.append(prod_df_retrofit)

    demand_val = load_dolphyn_ethylene_demand(balance_path) if os.path.exists(balance_path) else 0.0
    dolphyn_demand_rows.append({
        "Scenario":                   scen_short,
        "Plot_Category":              "Ethylene Demand",
        "Annual_Ethylene_Production": demand_val,
    })

    print(f"  Dolphyn {scen_short}: production = "
          f"{prod_df['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")
    
    print(f"  Dolphyn {scen_short}: production = "
          f"{prod_df_retrofit['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")

if dolphyn_production_tables:
    dolphyn_all = pd.concat(
        dolphyn_production_tables + [pd.DataFrame(dolphyn_demand_rows)],
        ignore_index=True,
    )
    dolphyn_combined_data = (
        dolphyn_all
        .groupby(["Scenario", "Plot_Category"])["Annual_Ethylene_Production"]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )
else:
    dolphyn_combined_data = pd.DataFrame(index=scenario_names)


# ---------------------------------------------------------------------
# MACRO: load from annual_flows_balance_Ethylene.csv
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

    macro_eth["Annual_Flow"] = pd.to_numeric(
        macro_eth["Annual_Flow"], errors="coerce"
    ).fillna(0.0)

    macro_eth["Plot_Category"] = macro_eth["Category"]

    macro_eth = macro_eth[macro_eth["Plot_Category"].notna()].copy()
    macro_eth_tables.append(macro_eth)

    print(f"  MACRO {scen_short}: {len(macro_eth)} rows loaded")


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
else:
    macro_combined_data = pd.DataFrame(index=scenario_names)

for scen_short, scen_path in macro_scenario_paths.items():
    if scen_short in macro_combined_data.index:
        # NSD file values are in the same raw units as Annual_Flow (no conversion)
        nsd = load_annual_nsd(scen_path, "ethylene_demand_")
        macro_combined_data.loc[scen_short, "Non-Served Demand"] = nsd


# ---------------------------------------------------------------------
# Align columns for both models
# ---------------------------------------------------------------------

for col in desired_order:
    if col not in dolphyn_combined_data.columns:
        dolphyn_combined_data[col] = 0.0
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

dolphyn_combined_data = (
    dolphyn_combined_data.reindex(scenario_names).fillna(0.0)[desired_order]
)
macro_combined_data = (
    macro_combined_data.reindex(scenario_names).fillna(0.0)[desired_order]
)

print("\nDolphyn ethylene balance by scenario (t/yr):")
print(dolphyn_combined_data)

print("\nMACRO ethylene balance by scenario (t/yr):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario (MACRO)
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
# Existing steam cracker capacity (same calculation as ETHYLENE_Macro.py)
# ---------------------------------------------------------------------

_t_ethane_p_t_ethylene = 1.4277269  # t-ethane/t-ethylene
_mwh_ethane_p_t_ethane = 14.41666667      # MWh-ethane/t-ethane (LHV)

# Strip the trailing "/results_NNN/results" the same way Step_1's
# macro_input_paths does, but computed locally from our own manual
# macro_scenario_paths so this doesn't depend on Step_1's scenario list.
_macro_input_path = re.sub(
    r"/results_\d+/results$", "", macro_scenario_paths[scenario_names[0]]
)

_crackers_json_path = os.path.join(
    macro_base_dir,
    _macro_input_path,
    "assets",
    "existing_steam_crackers.json",
)
with open(_crackers_json_path) as _f:
    _crackers = json.load(_f)

_total_cap_mwh_per_hr = sum(
    inst["edges"]["ethane_consumption_edge"]["existing_capacity"]
    for asset in _crackers["steamcracker_existing"]
    for inst in asset["instance_data"]
)

existing_cracker_cap = (
    _total_cap_mwh_per_hr / _mwh_ethane_p_t_ethane / _t_ethane_p_t_ethylene * 8760
)


# ---------------------------------------------------------------------
# Build paired plotting table (same logic as LF paired plot)
# ---------------------------------------------------------------------

plot_rows  = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(dolphyn_combined_data.loc[scen, desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, desired_order])
    plot_index.append((scen, "MACRO"))

plot_df = pd.DataFrame(plot_rows)
plot_df.index = pd.MultiIndex.from_tuples(
    plot_index, names=["Scenario", "Model"]
)

y_tick_labels = [
    "D" if model == "Dolphyn" else "M"
    for _, model in plot_df.index
]


# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.2, 4.4))

pair_gap   = 0.45
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

# Reposition bars to create gaps between scenario pairs and apply hatches
for container, col in zip(ax.containers, desired_order):
    hatch = category_hatch.get(col, "")
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)
        patch.set_hatch(hatch)
        patch.set_edgecolor("white" if hatch else "none")

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Ethylene Balance (t/yr)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
#ax.axvline(x=existing_cracker_cap, color="red", linewidth=1.5, linestyle="--",
#           label="Total Existing Capacity")
#ax.axvline(x=0.8 * existing_cracker_cap, color="red", linewidth=1, linestyle=":",
#           label="80% Existing Capacity")

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

ax.set_ylim(max(bar_positions) + 0.8, -0.8)

handles, labels = ax.get_legend_handles_labels()
label_to_handle = dict(zip(labels, handles))

custom_handles = [label_to_handle[col] for col in desired_order if col in label_to_handle]
custom_labels  = [label_map[col]       for col in desired_order if col in label_to_handle]
if "Total Existing Capacity" in label_to_handle:
    custom_handles.append(label_to_handle["Total Existing Capacity"])
    custom_labels.append("Total Existing Capacity")
##if "80% Existing Capacity" in label_to_handle:
 #   custom_handles.append(label_to_handle["80% Existing Capacity"])
 #   custom_labels.append("80% Existing Capacity")

ax.legend(
    custom_handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.28),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.24, right=0.98, top=0.88, bottom=0.40)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------
y_plotly_labels = [
    f"{scen} ({'D' if model == 'Dolphyn' else 'M'})"
    for scen, model in plot_df.index
]

_plotly_hatch_map = {"//": "/", "..": "."}

fig_plotly = go.Figure()

for col in desired_order:
    display_name = label_map.get(col, col)
    color = category_colors.get(col, '#333333')
    pattern_shape = _plotly_hatch_map.get(category_hatch.get(col, ""), "")
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=y_plotly_labels,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=color,
        marker_pattern_shape=pattern_shape,
        marker_pattern_fgcolor="white",
        marker_pattern_fillmode="overlay",
        hovertemplate='%{fullData.name}: %{x:,.0f} t/yr<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Ethylene Balance (t/yr)',
    xaxis_title='t/yr',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[
        dict(type='line', x0=0, x1=0, y0=-0.5,
             y1=len(plot_df) - 0.5, yref='y',
             line=dict(color='black', width=1, dash='dash')),
        #dict(type='line', x0=existing_cracker_cap, x1=existing_cracker_cap,
        #     y0=-0.5, y1=len(plot_df) - 0.5, yref='y',
        #     line=dict(color='red', width=1.5, dash='dash')),
        #dict(type='line', x0=0.8 * existing_cracker_cap, x1=0.8 * existing_cracker_cap,
        #     y0=-0.5, y1=len(plot_df) - 0.5, yref='y',
        #     line=dict(color='red', width=1, dash='dot')),
    ],
    #annotations=[
    #    dict(x=existing_cracker_cap, y=len(plot_df) - 0.5,
    #         xref='x', yref='y', yanchor='bottom',
    #         text='Total Existing Capacity', showarrow=False,
    #         font=dict(color='red', size=11)),
    #    dict(x=0.8 * existing_cracker_cap, y=len(plot_df) - 0.5,
    #         xref='x', yref='y', yanchor='bottom',
    #         text='80% Existing Capacity', showarrow=False,
    #         font=dict(color='red', size=11)),
    #],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ethylene_d_vs_m_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')