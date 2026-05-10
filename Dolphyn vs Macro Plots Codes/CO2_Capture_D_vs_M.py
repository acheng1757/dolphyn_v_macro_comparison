#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

scenario_names = ["HB-HS", "HB-LS", "LB-HS", "LB-LS"]

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, macro_base_dir

dolphyn_scenario_paths = {
    "HB-HS": "NineZones_High_Biomass_High_CO2",
    "HB-LS": "NineZones_High_Biomass_Low_CO2",
    "LB-HS": "NineZones_Low_Biomass_High_CO2",
    "LB-LS": "NineZones_Low_Biomass_Low_CO2",
}

macro_scenario_paths = {
    "HB-HS": "NineZones_High_Biomass_High_CO2/results_001/results",
    "HB-LS": "NineZones_High_Biomass_Low_CO2/results_001/results",
    "LB-HS": "NineZones_Low_Biomass_High_CO2/results_001/results",
    "LB-LS": "NineZones_Low_Biomass_Low_CO2/results_001/results",
}

# Dolphyn and MACRO captured CO2 values are treated as tonnes CO2.
TONNE_TO_MT = 1e-6


# ---------------------------------------------------------------------
# Plot categories
# ---------------------------------------------------------------------

# Dolphyn columns of interest
columns_of_interest = [
    "DAC Capture",
    "Bio Elec Capture",
    "Bio H2 Capture",
    "Bio LF Capture",
    "Bio NG Capture",
    "Synfuel Plant Capture",
    "Synfuel Plant Consumption",
    "Syn NG Plant Capture",
    "Syn NG Plant Consumption",
    "NG Power CCS",
    "NG DAC CCS",
    "NG H2 CCS",
    "CO2 Storage",
]

combine_mapping = {
    "NG DAC CCS": "DAC Capture",

    "Bio Elec Capture": "Biomass Capture",
    "Bio H2 Capture": "Biomass Capture",
    "Bio LF Capture": "Biomass Capture",
    "Bio NG Capture": "Biomass Capture",

    "Syn NG Plant Capture": "Synthetic NG",
    "Syn NG Plant Consumption": "Synthetic NG",

    "Synfuel Plant Capture": "Synthetic Fuels",
    "Synfuel Plant Consumption": "Synthetic Fuels",
}

desired_order = [
    "CO2 Storage",
    "Synthetic Fuels",
    "Synthetic NG",
    "NG Power CCS",
    "NG H2 CCS",
    "DAC Capture",
    "Biomass Capture",
]

category_colors = {
    "Biomass Capture": "olivedrab",
    "DAC Capture": "darkblue",
    "NG Power CCS": "orange",
    "NG H2 CCS": "deepskyblue",
    "Synthetic Fuels": "purple",
    "Synthetic NG": "violet",
    "CO2 Storage": "darkgoldenrod",
}

category_names = {
    "CO2 Storage": "CO2 Storage",
    "Synthetic NG": "Syn. NG",
    "Synthetic Fuels": "Syn. Liquids",
    "NG Power CCS": "Power CCS",
    "NG H2 CCS": "H2 CCS",
    "DAC Capture": "DAC",
    "Biomass Capture": "BECCS",
}


# ---------------------------------------------------------------------
# Dolphyn captured CO2 balance
# ---------------------------------------------------------------------

dolphyn_file_paths = [
    os.path.join(
        dolphyn_base_dir,
        dolphyn_scenario_paths["HB-HS"],
        "Results/Results_CSC/Zone_CO2_storage_balance.csv",
    ),
    os.path.join(
        dolphyn_base_dir,
        dolphyn_scenario_paths["HB-LS"],
        "Results/Results_CSC/Zone_CO2_storage_balance.csv",
    ),
    os.path.join(
        dolphyn_base_dir,
        dolphyn_scenario_paths["LB-HS"],
        "Results/Results_CSC/Zone_CO2_storage_balance.csv",
    ),
    os.path.join(
        dolphyn_base_dir,
        dolphyn_scenario_paths["LB-LS"],
        "Results/Results_CSC/Zone_CO2_storage_balance.csv",
    ),
]

global_values_per_scenario = {}

for path, scenario in zip(dolphyn_file_paths, scenario_names):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dolphyn captured CO2 balance file not found: {path}")

    df = pd.read_csv(path, header=0)
    df.columns = df.columns.str.strip()

    annual_sum_row = df[df.iloc[:, 0] == "AnnualSum"]

    if not annual_sum_row.empty:
        global_values = {}

        for col in columns_of_interest:
            col_values = (
                annual_sum_row
                .filter(like=col, axis=1)
                .apply(pd.to_numeric, errors="coerce")
                .fillna(0.0)
                .sum(axis=1)
                .values
                * TONNE_TO_MT
            )

            global_values[col] = col_values[0] if col_values.size > 0 else 0.0

    else:
        global_values = {col: 0.0 for col in columns_of_interest}

    global_values_per_scenario[scenario] = global_values

dolphyn_combined_data = pd.DataFrame(global_values_per_scenario).T
dolphyn_combined_data = dolphyn_combined_data.reindex(scenario_names).fillna(0.0)

# Combine detailed Dolphyn columns into plotting categories
dolphyn_combined_data = dolphyn_combined_data.rename(columns=combine_mapping)
dolphyn_combined_data = dolphyn_combined_data.T.groupby(level=0).sum().T

for col in desired_order:
    if col not in dolphyn_combined_data.columns:
        dolphyn_combined_data[col] = 0.0

dolphyn_combined_data = dolphyn_combined_data[desired_order]


# ---------------------------------------------------------------------
# MACRO captured CO2 balance
# ---------------------------------------------------------------------

def map_macro_captured_co2_category(row):
    """
    Map MACRO captured CO2 balance rows to plotting categories.

    MACRO is grouped by Sector, except Synthetic fuels:
      - if Edge contains Syn_NG, assign to Synthetic NG
      - otherwise assign to Synthetic Fuels
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
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

    return None


macro_tables = []

for scen_short, scen_path in macro_scenario_paths.items():

    # Use Captured_CO2 file if that is your balance-specific filename.
    # If your local file is named annual_flows_balance_CO2.csv instead,
    # this fallback will also work.
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
# Optional checks
# ---------------------------------------------------------------------

print("\nDolphyn captured CO2 balance by scenario (Mt):")
print(dolphyn_combined_data)

print("\nMACRO captured CO2 balance by scenario (Mt):")
print(macro_combined_data)

print("\nDolphyn net captured CO2 balance by scenario (Mt):")
print(dolphyn_combined_data.sum(axis=1))

print("\nMACRO net captured CO2 balance by scenario (Mt):")
print(macro_combined_data.sum(axis=1))


# ---------------------------------------------------------------------
# Build paired plotting table
# ---------------------------------------------------------------------

plot_rows = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(dolphyn_combined_data.loc[scen, desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, desired_order])
    plot_index.append((scen, "MACRO"))

plot_df = pd.DataFrame(plot_rows)
plot_df.index = pd.MultiIndex.from_tuples(
    plot_index,
    names=["Scenario", "Model"],
)

y_tick_labels = [
    "D" if model == "Dolphyn" else "M"
    for _, model in plot_df.index
]


# ---------------------------------------------------------------------
# Plot Dolphyn and MACRO captured CO2 balance side by side
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.0, 3.4))

pair_gap = 0.45
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

# Move bars from default positions 0, 1, 2, ... to custom positions with gaps
for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Captured CO2 Balance (Mt)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-1250, 1250)
ax.set_xticks([-1000, -500, 0, 500, 1000])
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

# Keep HB-HS at the top
ax.set_ylim(max(bar_positions) + 0.8, -0.8)

# Optional: add target storage indicators, same as previous Dolphyn-only plot
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
        y_dolphyn = i * (2 + pair_gap)
        y_macro = y_dolphyn + 1

        ax.barh(
            y_dolphyn,
            20,
            height=indicator_height,
            color="black",
            alpha=0.8,
            left=target_value,
        )

        ax.barh(
            y_macro,
            20,
            height=indicator_height,
            color="black",
            alpha=0.8,
            left=target_value,
        )

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

plt.subplots_adjust(left=0.24, right=0.98, top=0.88, bottom=0.36)

plt.show()