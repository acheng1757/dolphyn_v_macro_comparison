#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import sys
import re

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

scenario_names = ["Ethylene_Case"]

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, macro_base_dir, macro_results_folder, dolphyn_results_folder

dolphyn_scenario_paths = {
    "Ethylene_Case": "Ethylene_Case",
}

macro_scenario_paths = {
    "Ethylene_Case": f'Ethylene_Case/{macro_results_folder}/results',
}

# Ethylene flows are already in tonnes — no conversion needed for either model.


# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "TSC NGfuel",
    "Ret+TSC NGfuel",

    "TSC CC90 NGfuel",
    "Ret+TSC CC90 NGfuel",

    "TSC NGfuel H2out",
    "Ret+TSC NGfuel H2out",

    "TSC CC90 NGfuel H2out",
    "Ret+TSC CC90 NGfuel H2out",

    "TSC H2fuel",
    "Ret+TSC H2fuel",

    "TSC H2fuel CH4out",
    "Ret+TSC H2fuel CH4out",

    "Electric SC",
    "Ret+Electric SC",
    
    "Dehydration NGfuel",
    "Dehydration H2fuel",
    "Synthetic H2fuel",
    "Synthetic CC90 H2fuel",
    "Ethylene Demand",
]

category_colors = {
    # Base assets
    "TSC NGfuel":                "#e8630a",   # vivid orange
    "TSC CC90 NGfuel":           "#7a2e0e",   # deep brick (CCS = darker)
    "TSC NGfuel H2out":          "#f5c518",   # bright gold
    "TSC CC90 NGfuel H2out":     "#a07c00",   # dark gold (CCS = darker)
    "TSC H2fuel":                "#3a8fd1",   # sky blue
    "TSC H2fuel CH4out":         "#1a4f80",   # navy (CH4 out = darker)
    "Electric SC":               "#18b4a0",   # teal
    # Retrofit variants — lighter versions of their base
    "Ret+TSC NGfuel":            "#f4a86a",   # light orange
    "Ret+TSC CC90 NGfuel":       "#b5603a",   # mid brick
    "Ret+TSC NGfuel H2out":      "#fae27a",   # light gold
    "Ret+TSC CC90 NGfuel H2out": "#d4b840",   # mid gold
    "Ret+TSC H2fuel":            "#85c4ec",   # light sky blue
    "Ret+TSC H2fuel CH4out":     "#4a7faf",   # mid navy
    "Ret+Electric SC":               "#18b4a0",   # teal
    # Dehydration
    "Dehydration NGfuel":        "#57c46a",   # medium green
    "Dehydration H2fuel":        "#1a6e30",   # dark green (H2 = darker)
    # Synthetic
    "Synthetic H2fuel":          "#9b59b6",   # purple
    "Synthetic CC90 H2fuel":     "#4a1a6e",   # deep purple (CCS = darker)
    # Demand
    "Ethylene Demand":           "#5a6fa8",   # slate blue
}

label_map = {
    "TSC NGfuel":                "TSC NGfuel",
    "TSC CC90 NGfuel":           "TSC CC90 NGfuel",
    "TSC NGfuel H2out":          "TSC NGfuel H2out",
    "TSC CC90 NGfuel H2out":     "TSC CC90 NGfuel H2out",
    "TSC H2fuel":                "TSC H2fuel",
    "TSC H2fuel CH4out":         "TSC H2fuel CH4out",
    "Electric SC":               "Electric SC",
    "Ret+TSC NGfuel":            "Ret+TSC NGfuel",
    "Ret+TSC CC90 NGfuel":       "Ret+TSC CC90 NGfuel",
    "Ret+TSC NGfuel H2out":      "Ret+TSC NGfuel H2out",
    "Ret+TSC CC90 NGfuel H2out": "Ret+TSC CC90 NGfuel H2out",
    "Ret+TSC H2fuel":            "Ret+TSC H2fuel",
    "Ret+TSC H2fuel CH4out":     "Ret+TSC H2fuel CH4out",
    "Ret+Electric SC":               "Ret+Electric SC",
    "Dehydration NGfuel":        "Dehydration NGfuel",
    "Dehydration H2fuel":        "Dehydration H2fuel",
    "Synthetic H2fuel":          "Synthetic H2fuel",
    "Synthetic CC90 H2fuel":     "Synthetic CC90 H2fuel",
    "Ethylene Demand":           "Ethylene Demand",
}

# ---------------------------------------------------------------------
# Dolphyn: load production from Ethylene_capacity.csv
# ---------------------------------------------------------------------

RESOURCE_CATEGORY_MAP = {
    # new build assets
    "F-CC90-NGin-H2out":  "TSC CC90 NGfuel H2out",
    "F-NGin-H2out":       "TSC NGfuel H2out",
    "F-H2in-CH4out":      "TSC H2fuel CH4out",
    "S-CC90-H2in":        "Synthetic CC90 H2fuel",
    "F-CC90-NGin":        "TSC CC90 NGfuel",
    "F-NGin":             "TSC NGfuel",
    "F-H2in":             "TSC H2fuel",
    "F-Ein":              "Electric SC",
    "S-H2in":             "Synthetic H2fuel",
    "B-NGin":             "Dehydration NGfuel",
    "B-H2in":             "Dehydration H2fuel",

    # existing assets
    "TSC: H2":             "TSC NGfuel H2out",

    # retrofit assets
    "TSC+H2in:CH4":       "TSC H2fuel CH4out",
    "TSC":  "TSC NGfuel",
    "TSC+CC90": "TSC CC90 NGfuel",
    "TSC+CC90: H2": "TSC NGfuel H2out",
    "TSC+H2in": "TSC H2fuel",
    "ESC": "Electric SC",
}

def categorize_ethylene_resource(resource):
    return RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None)

# load production for new build assets
def load_ethylene_production_new_build(capacity_path, scenario):
    df = pd.read_csv(capacity_path)
    df.columns = df.columns.str.strip()
    df = df[df["Resource"] != "Total"].copy()

    df["Annual_Ethylene_Production"] = pd.to_numeric(
        df["Annual_Ethylene_Production"], errors="coerce"
    ).fillna(0.0)

    # Zero out optimizer noise — real values are 1e5+ tonnes
    df.loc[df["Annual_Ethylene_Production"].abs() < 1.0,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    df = df[df["Plot_Category"].notna()].copy()
    df["Scenario"] = scenario

    return df[["Scenario", "Plot_Category", "Annual_Ethylene_Production"]]

def load_ethylene_production_existing(capacity_path, scenario):

    # Read true asset names from raw header (before pandas adds .1, .2 suffixes)
    with open(capacity_path) as f:
        raw_header = f.readline().strip().split(",")
    resource_names = [col.strip() for col in raw_header[1:]]  # skip the index column

    df_raw = pd.read_csv(capacity_path, header=0, index_col=0)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw.index = df_raw.index.str.strip()

    # Pivot AnnualSum row into a Resource/Value DataFrame
    annual_row = df_raw.loc["AnnualSum"]

    df = pd.DataFrame({
        "Resource": resource_names,
        "Annual_Ethylene_Production": pd.to_numeric(annual_row.values, errors="coerce"),
    }).fillna(0.0)

    print("Raw resource names from CSV:")
    print(df["Resource"].tolist())

    # Zero out optimiser noise — real values are 1e5+ tonnes, noise is 1e-6 or below
    noise_threshold = 1.0
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    print(df["Resource"])

    df = df[df["Plot_Category"].notna()].copy()

    df["Scenario"] = scenario
    return df[["Scenario", "Plot_Category", "Annual_Ethylene_Production"]]

def load_ethylene_production_retrofit(capacity_path, scenario):
    """
    Read Ethylene_Retrofit_Balance.csv and return a DataFrame with columns:
        Scenario, Plot_Category, Annual_Ethylene_Production
    Assets with unmapped resource names are dropped.
    Near-zero values (optimiser noise) are zeroed out.
    """
    with open(capacity_path) as f:
        raw_header = f.readline().strip().split(",")
    resource_names = [col.strip() for col in raw_header[1:]]  # skip index column

    df_raw = pd.read_csv(capacity_path, header=0, index_col=0)
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
        lambda r: "Ret+" + categorize_ethylene_resource(r)
        if categorize_ethylene_resource(r) is not None
        else None
    )
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
    results_dir  = os.path.join(dolphyn_base_dir, scen_path, dolphyn_results_folder, "Results_Ethylene")
    capacity_path = os.path.join(results_dir, "Ethylene_capacity.csv")
    balance_path  = os.path.join(results_dir, "Ethylene_Balance.csv")
    existing_balance_path = os.path.join(results_dir, "Ethylene_Plant_Balance.csv")
    retrofit_balance_path = os.path.join(results_dir, "Ethylene_Retrofit_Balance.csv")

    if not os.path.exists(capacity_path):
        print(f"Warning: Ethylene_capacity.csv not found: {capacity_path}")
        continue

    prod_df_new_build = load_ethylene_production_new_build(capacity_path, scen_short)
    prod_df_existing = load_ethylene_production_existing(existing_balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit(retrofit_balance_path, scen_short)

    dolphyn_production_tables.append(prod_df_new_build)
    dolphyn_production_tables.append(prod_df_existing)
    dolphyn_production_tables.append(prod_df_retrofit)

    demand_val = load_dolphyn_ethylene_demand(balance_path) if os.path.exists(balance_path) else 0.0
    dolphyn_demand_rows.append({
        "Scenario":                   scen_short,
        "Plot_Category":              "Ethylene Demand",
        "Annual_Ethylene_Production": demand_val,
    })

    print(f"  Dolphyn {scen_short}: production = "
          f"{prod_df_new_build['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")
    
    print(f"  Dolphyn {scen_short}: production = "
          f"{prod_df_existing['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
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
'''
# takes in the raw labels and remaps to desired categories
def map_macro_ethylene_category(row):
    sector   = str(row.get("Sector",   "")).strip()
    category = str(row.get("Category", "")).strip()
    edge     = str(row.get("Edge",     "")).strip().lower()

    if sector.lower() == "demand":
        return "Ethylene Demand"

    if sector.lower() == "ethylene":
        if category == "Electric Steam Cracker":
            return "Electric Steam Cracker"
        if category == "Thermal Steam Cracker":
            return "Thermal Steam Cracker"
        if category == "Ethanol Dehydration":
            return "Ethanol Dehydration"
        if category == "Synthetic Ethylene":
            return "Synthetic Ethylene"

    # Fallback: infer from edge name
    if "f_ein" in edge or "f-ein" in edge:
        return "Electric Steam Cracker"
    if any(x in edge for x in ["f_ngin", "f-ngin", "f_cc90", "f-cc90",
                                 "f_h2in", "f-h2in"]):
        return "Thermal Steam Cracker"
    if any(x in edge for x in ["b_ngin", "b-ngin", "b_h2in", "b-h2in"]):
        return "Ethanol Dehydration"
    if any(x in edge for x in ["s_h2in", "s-h2in", "s_cc90", "s-cc90"]):
        return "Synthetic Ethylene"

    return None
'''

ETHYLENE_CATEGORIES = [
    ("TSC NGfuel H2out", [           # H2out before plain NGfuel
        r"_F(-|_)NGin(-|_)H2out_ethylene",
    ]),
    ("TSC NGfuel", [
        r"_F(-|_)NGin_ethylene",
    ]),
    ("Ret+TSC NGfuel H2out", [       # H2out before plain NGfuel
        r"_F(-|_)NGin(-|_)H2out_RETROFIT_ethylene",
    ]),
    ("Ret+TSC NGfuel", [
        r"_F(-|_)NGin_RETROFIT_ethylene",
    ]),
    ("TSC CC90 NGfuel H2out", [      # H2out before plain CC90 NGfuel
        r"_F(-|_)CC90(-|_)NGin(-|_)H2out_ethylene",
    ]),
    ("TSC CC90 NGfuel", [
        r"_F(-|_)CC90(-|_)NGin_ethylene",
    ]),
    ("Ret+TSC CC90 NGfuel H2out", [  # H2out before plain CC90 NGfuel
        r"_F(-|_)CC90(-|_)NGin(-|_)H2out_RETROFIT_ethylene",
    ]),
    ("Ret+TSC CC90 NGfuel", [
        r"_F(-|_)CC90(-|_)NGin_RETROFIT_ethylene",
    ]),
    ("TSC H2fuel CH4out", [          # CH4out before plain H2fuel
        r"_F(-|_)H2in(-|_)CH4out_ethylene",
    ]),
    ("TSC H2fuel", [
        r"_F(-|_)H2in_ethylene",
    ]),
    ("Ret+TSC H2fuel CH4out", [      # CH4out before plain H2fuel
        r"_F(-|_)H2in(-|_)CH4out_RETROFIT_ethylene",
    ]),
    ("Ret+TSC H2fuel", [
        r"_F(-|_)H2in_RETROFIT_ethylene",
    ]),
    ("Ret+Electric SC", [
        r"(-|_)F(-|_)Ein_RETROFIT_ethylene",
    ]),
    ("Electric SC", [
        r"(-|_)F(-|_)Ein_ethylene",
    ]),
    ("Synthetic CC90 H2fuel", [      # CC90 before plain Synthetic
        r"_S(-|_)CC90(-|_)H2in_ethylene",
    ]),
    ("Synthetic H2fuel", [
        r"_S(-|_)H2in_ethylene",
    ]),
    ("Dehydration NGfuel", [
        r"_B(-|_)NGin_ethylene",
    ]),
    ("Dehydration H2fuel", [
        r"_B(-|_)H2in_ethylene",
    ]),
]

# Pre-compile for performance
_COMPILED_ETHYLENE_CATEGORIES = [
    (label, [re.compile(pattern, re.IGNORECASE) for pattern in patterns])
    for label, patterns in ETHYLENE_CATEGORIES
]

def map_macro_ethylene_category(row):
    sector = str(row.get("Sector", "")).strip().lower()
    edge   = str(row.get("Edge",   "")).strip()

    if sector == "demand":
        return "Ethylene Demand"

    for label, compiled_patterns in _COMPILED_ETHYLENE_CATEGORIES:
        if any(pat.search(edge) for pat in compiled_patterns):
            return label

    return None

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

    macro_eth["Annual_Flow"] = pd.to_numeric(
        macro_eth["Annual_Flow"], errors="coerce"
    ).fillna(0.0)

    macro_eth["Scenario"] = scen_short

    macro_eth["Plot_Category"] = macro_eth.apply(
        map_macro_ethylene_category, axis=1
    )

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

# Reposition bars to create gaps between scenario pairs
for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Ethylene Balance (t/yr)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

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

ax.set_ylim(max(bar_positions) + 0.8, -0.8)

handles, _ = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.28),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.24, right=0.98, top=0.88, bottom=0.40)

plt.show()