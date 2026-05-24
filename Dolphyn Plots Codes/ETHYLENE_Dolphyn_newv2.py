#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import sys
import re

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, macro_results_folder, dolphyn_results_folder, scenario_names

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

dolphyn_scenario_paths = {
    "new_11w_test": f'new_11w_test/{dolphyn_results_folder}/Results_Ethylene',
}

# Ethylene_capacity.csv Annual_Ethylene_Production is in tonnes/year already.


# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "TSC",
    "Ret-TSC",
    "Existing Capacities",

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
    
    "Existing Capacities":  "#cccccc",   # light gray
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

    "Existing Capacities":  "Existing Capacities",

    "Dehydration NGfuel":   "Dehydration NGfuel",
    "Dehydration H2fuel":   "Dehydration H2fuel",
    "Ethylene Demand":      "Ethylene Demand",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC", # confirm grouping
}

# ---------------------------------------------------------------------
# Resource → plot category mapping
# ---------------------------------------------------------------------
"""
# Resources that map to each plot category.
# Based on actual Dolphyn Ethylene_capacity.csv resource names.
THERMAL_RESOURCES   = {"CSC_Plant", "CSC_CCS_Plant"}
ELECTRIC_RESOURCES  = {"ESC_Plant"}
ETHANOL_RESOURCES   = {"Ethanol_Plant", "Ethanol_CCS_Plant"}
SYNTHETIC_RESOURCES = {
    "CO2_MS_MTO", "CO2_CTM_OCM", "CO2_DFT",
    "CO2_HTeCO_SFT", "CO2_eCO_SFT", "CO2_eCH4_OCM",
    "CO2_HTeCO_SeC2H4", "CO2_eCO_SeC2H4", "CO2_DeC2H4",
}

def categorize_ethylene_resource(resource):
    if resource in THERMAL_RESOURCES:
        return "Thermal Steam Cracker"
    if resource in ELECTRIC_RESOURCES:
        return "Electric Steam Cracker"
    if resource in ETHANOL_RESOURCES:
        return "Ethanol Dehydration"
    if resource in SYNTHETIC_RESOURCES:
        return "Synthetic Ethylene"
    return None
"""

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
    print('resource: ', resource)
    print('category: ', RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None))
    return RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None)

# ---------------------------------------------------------------------
# Load production from Ethylene_Balance.csv for EXISTING ASSETS + NEW BUILD ASSETS
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Load production from Ethylene_Retrofit_Balance.csv for RETROFITTED ASSETS
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Load demand from Ethylene_Balance.csv
# ---------------------------------------------------------------------

def load_ethylene_demand(balance_path, scenario):
    """
    Read Ethylene_Balance.csv and return total annual ethylene demand
    (summed across all zones) as a negative value in tonnes/year.

    The file has a multi-row header:
        Row 0: resource names (repeated per zone) — 'Ethylene Demand' marks demand cols
        Row 1: zone numbers
        Row 2: AnnualSum values
        Row 3+: per-timestep values

    Demand values in the file are already negative.
    """
    df = pd.read_csv(balance_path, header=None)

    resource_row = df.iloc[0].tolist()
    annualsum_row = df[df.iloc[:, 0] == "AnnualSum"]

    if annualsum_row.empty:
        print(f"  Warning: no AnnualSum row found in {balance_path}")
        return 0.0

    # Case-insensitive match on anything containing 'demand'
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
# Main loading loop
# ---------------------------------------------------------------------

production_tables = []
demand_rows = []

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

    # Production
    prod_df = load_ethylene_production(balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit(balance_retrofit_path, scen_short)
    production_tables.append(prod_df)
    production_tables.append(prod_df_retrofit)

    # Demand
    demand_val = load_ethylene_demand(balance_path, scen_short)
    demand_rows.append({
        "Scenario":    scen_short,
        "Plot_Category": "Ethylene Demand",
        "Annual_Ethylene_Production": demand_val,
    })

    print(f"  {scen_short}: total production = "
          f"{prod_df['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")

# ---------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------

if production_tables:
    all_rows = pd.concat(
        production_tables + [pd.DataFrame(demand_rows)],
        ignore_index=True,
    )

    combined_data = (
        all_rows
        .groupby(["Scenario", "Plot_Category"])["Annual_Ethylene_Production"]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )
else:
    combined_data = pd.DataFrame(index=scenario_names)

# Ensure all columns exist
for col in desired_order:
    if col not in combined_data.columns:
        combined_data[col] = 0.0

combined_data = combined_data[desired_order]

print("\nDolphyn ethylene balance by scenario (tonnes/year):")
print(combined_data)


# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------

plot_df = combined_data.copy()

# Only plot columns with non-zero values, in desired order
active_cols = [col for col in desired_order if combined_data[col].abs().sum() > 0]

fig, ax = plt.subplots(figsize=(5.2, 3.2))

# Rename columns to label_map values so pandas legend uses display names
plot_df[active_cols].rename(columns=label_map).plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in active_cols],
)

ax.set_yticklabels(scenario_names, fontsize=14)
ax.set_ylabel("")
ax.set_title("Ethylene Balance (t/yr)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
ax.invert_yaxis()

plt.subplots_adjust(left=0.20, right=0.98, top=0.92, bottom=0.12)
plt.savefig("ethylene_balance.png", bbox_inches="tight", dpi=150)
plt.show()