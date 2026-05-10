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
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, macro_results_folder, dolphyn_results_folder

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

scenario_names = ["Ethylene_Case"]

dolphyn_scenario_paths = {
    "Ethylene_Case": f'Ethylene_Case/{dolphyn_results_folder}/Results_Ethylene',
}

# Ethylene_capacity.csv Annual_Ethylene_Production is in tonnes/year already.


# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Thermal SC NGfuel",
    "Thermal SC CC90 NGfuel",
    "Thermal SC NGfuel H2out",
    "Thermal SC CC90 NGfuel H2out",
    "Thermal SC H2fuel",
    "Thermal SC H2fuel CH4out",
    "Electric SC",
    "Dehydration NGfuel",
    "Dehydration H2fuel",
    "Synthetic H2fuel",
    "Synthetic CC90 H2fuel",
    "Ethylene Demand",
]

category_colors = {
    "Thermal SC NGfuel":              "#e8630a",   # vivid orange
    "Thermal SC CC90 NGfuel":         "#7a2e0e",   # deep brick (CCS = darker)
    "Thermal SC NGfuel H2out":        "#f5c518",   # bright gold
    "Thermal SC CC90 NGfuel H2out":   "#a07c00",   # dark gold (CCS = darker)
    "Thermal SC H2fuel":              "#3a8fd1",   # sky blue
    "Thermal SC H2fuel CH4out":       "#1a4f80",   # navy blue (CH4 out = darker)
    "Electric SC":                    "#18b4a0",
    "Dehydration NGfuel":             "#57c46a",   # medium green
    "Dehydration H2fuel":             "#1a6e30",   # dark green (H2 = darker)
    "Synthetic H2fuel":               "#9b59b6",
    "Synthetic CC90 H2fuel":          "#4a1a6e",   # deep purple (CCS = darker)
    "Ethylene Demand":                "#5a6fa8",
}

label_map = {
    "Thermal SC NGfuel":              "Thermal SC NGfuel",
    "Thermal SC CC90 NGfuel":         "Thermal SC CC90 NGfuel",
    "Thermal SC NGfuel H2out":        "Thermal SC NGfuel H2out",
    "Thermal SC CC90 NGfuel H2out":   "Thermal SC CC90 NGfuel H2out",
    "Thermal SC H2fuel":              "Thermal SC H2fuel",
    "Thermal SC H2fuel CH4out":       "Thermal SC H2fuel CH4out",
    "Electric SC":                    "Electric SC",
    "Dehydration NGfuel":             "Dehydration NGfuel",
    "Dehydration H2fuel":             "Dehydration H2fuel",
    "Synthetic H2fuel":               "Synthetic H2fuel",
    "Synthetic CC90 H2fuel":          "Synthetic CC90 H2fuel",
    "Ethylene Demand":                "Ethylene Demand",
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

RESOURCE_CATEGORY_MAP = {
    "F-CC90-NGin-H2out":  "Thermal SC CC90 NGfuel H2out",
    "F-NGin-H2out":       "Thermal SC NGfuel H2out",
    "F-H2in-CH4out":      "Thermal SC H2fuel CH4out",
    "S-CC90-H2in":        "Synthetic CC90 H2fuel",
    "F-CC90-NGin":        "Thermal SC CC90 NGfuel",
    "F-NGin":             "Thermal SC NGfuel",
    "F-H2in":             "Thermal SC H2fuel",
    "F-Ein":              "Electric SC",
    "S-H2in":             "Synthetic H2fuel",
    "B-NGin":             "Dehydration NGfuel",
    "B-H2in":             "Dehydration H2fuel",
    "TSC: H2":             "Thermal SC NGfuel H2out",

    "TSC+H2in:CH4":       "Thermal SC H2fuel CH4out",
    "TSC":  "Thermal SC NGfuel",
    "TSC+CC90": "Thermal SC CC90 NGfuel",
    "TSC+CC90: H2": "Thermal SC NGfuel H2out",
    "TSC+H2in": "Thermal SC H2fuel",
    "ESC": "Electric SC",
}

def categorize_ethylene_resource(resource):
    return RESOURCE_CATEGORY_MAP.get(str(resource).strip(), None)

# ---------------------------------------------------------------------
# Load production from Ethylene_capacity.csv for NEW BUILD ASSETS
# ---------------------------------------------------------------------

def load_ethylene_production_new_build(capacity_path, scenario):
    """
    Read Ethylene_capacity.csv and return a DataFrame with columns:
        Scenario, Plot_Category, Annual_Ethylene_Production
    Rows with Resource == 'Total' or unmapped resources are dropped.
    Near-zero values (optimizer noise) are zeroed out.
    """
    df = pd.read_csv(capacity_path)
    print("Raw resource names from CSV:")
    print(df["Resource"].tolist())
    df.columns = df.columns.str.strip()

    # Drop the Total summary row
    df = df[df["Resource"] != "Total"].copy()

    df["Annual_Ethylene_Production"] = pd.to_numeric(
        df["Annual_Ethylene_Production"], errors="coerce"
    ).fillna(0.0)

    # Zero out optimizer noise — real values are 1e5+ tonnes, noise is 1e-6 or below
    noise_threshold = 1.0  # tonnes/year — safely below smallest real value (~1e5)
    df.loc[df["Annual_Ethylene_Production"].abs() < noise_threshold,
           "Annual_Ethylene_Production"] = 0.0

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    print(df["Resource"])
    df = df[df["Plot_Category"].notna()].copy()

    df["Scenario"] = scenario
    return df[["Scenario", "Plot_Category", "Annual_Ethylene_Production"]]

# ---------------------------------------------------------------------
# Load production from Ethylene_capacity.csv for EXISTING ASSETS
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Load production from Ethylene_capacity.csv for RETROFITED ASSETS
# ---------------------------------------------------------------------
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

    df["Plot_Category"] = df["Resource"].apply(categorize_ethylene_resource)
    print(df["Resource"])

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
    capacity_path = os.path.join(results_dir, "Ethylene_capacity.csv")
    balance_path  = os.path.join(results_dir, "Ethylene_Balance.csv")
    existing_balance_path = os.path.join(results_dir, "Ethylene_Plant_Balance.csv")
    retrofit_balance_path = os.path.join(results_dir, "Ethylene_Retrofit_Balance.csv")

    if not os.path.exists(capacity_path):
        print(f"Warning: Ethylene_capacity.csv not found: {capacity_path}")
        continue

    if not os.path.exists(balance_path):
        print(f"Warning: Ethylene_Balance.csv not found: {balance_path}")

    # Production
    prod_df_new_build = load_ethylene_production_new_build(capacity_path, scen_short)
    prod_df_existing = load_ethylene_production_existing(existing_balance_path, scen_short)
    prod_df_retrofit = load_ethylene_production_retrofit(retrofit_balance_path, scen_short)

    production_tables.append(prod_df_new_build)
    production_tables.append(prod_df_existing)
    production_tables.append(prod_df_retrofit)

    # Demand
    demand_val = load_ethylene_demand(balance_path, scen_short)
    demand_rows.append({
        "Scenario":    scen_short,
        "Plot_Category": "Ethylene Demand",
        "Annual_Ethylene_Production": demand_val,
    })

    print(f"  {scen_short}: total production = "
          f"{prod_df_new_build['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")
    
    print(f"  {scen_short}: total production = "
          f"{prod_df_existing['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
          f"demand = {demand_val:,.0f} t/yr")
    
    print(f"  {scen_short}: total production = "
          f"{prod_df_retrofit['Annual_Ethylene_Production'].sum():,.0f} t/yr, "
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

fig, ax = plt.subplots(figsize=(5.2, 3.2))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)
ax.set_ylabel("")
ax.set_title("Ethylene Balance (t/yr)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
ax.invert_yaxis()

# Custom legend
handles, _ = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.30),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.40)

plt.show()