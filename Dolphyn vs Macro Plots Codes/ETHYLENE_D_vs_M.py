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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir, macro_results_folder,
    dolphyn_results_folder, scenario_names,
)

dolphyn_scenario_paths = {
    scenario_names[0]: f'all_demand_test/{dolphyn_results_folder}/Results_Ethylene',
}

macro_scenario_paths = {
    scenario_names[0]: f'clean_slate_5_25/results_168h_all/results',
}

# Ethylene flows are already in tonnes — no conversion needed for either model.


# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "TSC",
    "Ret-TSC",
    "Existing TSC:H2",

    "TSC+CC90",
    "Ret-TSC+CC90",

    "TSC:H2",
    "Ret-TSC:H2",

    "MS+MTO",

    "MS+MTO+CC90",

    "TSC+CC90:H2",
    "Ret-TSC+CC90:H2",

    "TSC+H2in",
    "Ret-TSC+H2in",

    "TSC+CC90+H2in",
    "Ret-TSC+CC90+H2in",

    "ESC",
    "Ret-ESC",

    "TSC+H2in:CH4",
    "Ret-TSC+H2in:CH4",

    "Dehydration NGfuel",
    "Dehydration H2fuel",
    "Ethylene Demand",
]

category_colors = {
    "TSC":                  "#e8630a",   # vivid orange
    "Ret-TSC":              "#f4a86a",   # light orange

    "TSC+CC90":             "#7a2e0e",   # deep brick
    "Ret-TSC+CC90":         "#b5603a",   # mid brick

    "TSC:H2":               "#f5c518",   # bright gold (H2out co-product)
    "Ret-TSC:H2":          "#fae27a",   # light gold

    "MS+MTO":               "#9b59b6",   # purple (synthetic)
    "MS+MTO+CC90":          "#4a1a6e",   # deep purple

    "TSC+CC90:H2":          "#a07c00",   # dark gold (CC90 + H2out)
    "Ret-TSC+CC90:H2":     "#d4b840",   # mid gold

    "TSC+H2in":             "#3a8fd1",   # sky blue (H2fuel input)
    "Ret-TSC+H2in":         "#85c4ec",   # light sky blue

    "TSC+H2in:CH4":         "#1a4f80",   # navy (H2fuel + CH4out)
    "Ret-TSC+H2in:CH4":     "#4a7faf",   # mid navy

    "TSC+CC90+H2in":        "midnightblue",   # navy (CC90 + H2fuel) — same family
    "Ret-TSC+CC90+H2in":    "navy",   # mid navy

    "Existing TSC:H2":  "#f5c518",   # light gray
    "ESC":              "#a0a0a0",   # mid gray
    "Ret-ESC":              "#a0a0a0",   # mid gray

    "Dehydration NGfuel":   "#57c46a",   # medium green
    "Dehydration H2fuel":   "#1a6e30",   # dark green
    "Ethylene Demand":      "#5a6fa8",   # slate blue
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

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC", # confirm grouping
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
    "Existing Capacities":            "Existing TSC:H2",
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
    ("TSC", [
            r"_F(-|_)NGin_ethylene",           # F-NGin without H2out (the underscore after prevents matching F-NGin-H2out)
        ]),
        ("Ret-TSC", [
            r"_F(-|_)NGin_RETROFIT_ethylene",
        ]),
        ("TSC:H2", [
            r"_F(-|_)NGin(-|_)H2out_ethylene",
        ]),
        ("Ret-TSC:H2", [
            r"_F(-|_)NGin(-|_)H2out_RETROFIT_ethylene",  # in case separator varies
        ]),
        ("TSC CC90 NGfuel", [
            r"_F(-|_)CC90(-|_)NGin_ethylene",
            r"TSC+CC90",
        ]),
        ("Ret+TSC CC90 NGfuel", [
            r"_F(-|_)CC90(-|_)NGin_RETROFIT_ethylene",
            r"Ret-TSC+CC90",
        ]),
        ("TSC+CC90:H2", [
            r"_F(-|_)CC90(-|_)NGin(-|_)H2out_ethylene",
        ]),
        ("Ret-TSC+CC90:H2", [
            r"_F(-|_)CC90(-|_)NGin(-|_)H2out_RETROFIT_ethylene",
        ]),
        ("TSC+H2in", [
            r"_F(-|_)H2in_ethylene",
        ]),
        ("Ret-TSC+H2in", [
            r"_F(-|_)H2in_RETROFIT_ethylene",
        ]),
        ("TSC+H2in:CH4", [
            r"_F(-|_)H2in(-|_)CH4out_ethylene",
            r"TSC+H2in:CH4",
        ]),
        ("Ret-TSC+H2in:CH4", [
            r"_F(-|_)H2in(-|_)CH4out_RETROFIT_ethylene",
            r"RET-TSC+H2in:CH4",
        ]),
        ("ESC", [
            r"(-|_)F(-|_)Ein_ethylene",
            r"ESC",
        ]),
        ("Ret-ESC", [
            r"(-|_)F(-|_)Ein_RETROFIT_ethylene",
        ]),
        ("MS+MTO", [
            r"_S(-|_)H2in_ethylene",           # S-H2in without CC90
        ]),
        ("MS+MTO+CC90", [
            r"_S(-|_)CC90(-|_)H2in_ethylene",
        ]),
        ("Dehydration NGfuel", [
            r"_B(-|_)NGin_ethylene",
            r"Bio-eth+CC88:NG",
        ]),
        ("Dehydration H2fuel", [
            r"_B(-|_)H2in_ethylene",
            r"Bio-eth+CC88:H2",
        ])
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