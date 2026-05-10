#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, macro_results_folder, scenario_names

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

macro_scenario_paths = {
    "Ethylene_Case": f"Ethylene_Case/{macro_results_folder}/results",
}

# Ethylene flows in flows.csv are already in tonnes — no conversion needed.

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

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [desired_order]
)

print("\nMACRO ethylene balance by scenario (tonnes):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

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
ax.set_title("Ethylene Balance (tonnes)", fontsize=16)
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
