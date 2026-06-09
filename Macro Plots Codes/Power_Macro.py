import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def map_macro_power_category(row):
    """
    Map MACRO annual_flows_balance_Power.csv rows to plotting categories.

    Small MACRO-only categories intentionally excluded:
      - storage losses
      - H2 turbines (H2 CCGT, H2 OCGT)
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Demand rows
    if sector == "Demand":
        return "Demand"

    # Power generation technologies
    if sector == "Power":
        if category in ["Hydro", "Nuclear", "NG", "NG CCS", "Solar", "Wind"]:
            return category

        # Exclude small MACRO-only categories from the plot
        if category in ["Battery", "H2 CCGT", "H2 OCGT"]:
            return None

        return None

    # Hydrogen-sector electricity consumption
    if sector == "Hydrogen":
        return "H2 Production"

    # CO2-sector electricity consumption
    if sector == "CO2":
        return "Sorbent DAC Input"

    # Bioenergy electricity consumption or credit
    if sector == "Bioenergy":
        return "Bioenergy Input"
    
    if sector == "Ethanol":
        return "Ethanol Input"
    
    if sector == "Ethylene":
        return "Ethylene Input"

    # Synthetic fuels
    if sector == "Synthetic fuels":
        if category == "S-NG":
            return "Synthetic NG"

        if category in ["S-J", "S-J-CC99", "S-J-99"]:
            return "Synthetic FT"

        return "Synthetic FT"

    if sector == "Transmission":
        return "Transmission"

    return None

# ---------------------------------------------------------------------
# Read MACRO electricity balance from annual_flows_balance_Power.csv
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Transmission",
    "H2 Production",
    "Sorbent DAC Input",
    "Bioenergy Input",
    "Ethylene Input",
    "Ethanol Input",
    "Synthetic FT",
    "Synthetic NG",
    "Hydro",
    "Nuclear",
    "NG",
    "NG CCS",
    "Solar",
    "Wind",
]

macro_power_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_power_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Power.csv",
    )

    if not os.path.exists(macro_power_path):
        print(f"Warning: MACRO power balance file not found: {macro_power_path}")
        continue

    macro_power = pd.read_csv(macro_power_path)
    macro_power.columns = macro_power.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_power.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_power_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_power.columns.tolist()}"
        )

    macro_power["Scenario"] = scen_short

    # Convert MWh to EJ
    macro_power["Annual_Flow"] = (
        pd.to_numeric(macro_power["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * conversion_factor
    )

    macro_power["Plot_Category"] = macro_power.apply(
        map_macro_power_category,
        axis=1,
    )

    macro_power = macro_power[macro_power["Plot_Category"].notna()].copy()

    macro_power_tables.append(macro_power)


if macro_power_tables:
    macro_power_combined = pd.concat(macro_power_tables, ignore_index=True)

    macro_combined_data = (
        macro_power_combined
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
# Print balance table for checking
# ---------------------------------------------------------------------

print("\nMACRO electricity balance by scenario (EJ):")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Electricity balance check:")
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
# Plot settings
# ---------------------------------------------------------------------

category_colors = {
    "Hydro": "steelblue",
    "Nuclear": "red",
    "NG": "#c0504d",
    "NG CCS": "silver",
    "Solar": "gold",
    "Wind": "dodgerblue",
    "Sorbent DAC Input": "darkblue",
    "Bioenergy Input": "seagreen",
    "Ethylene Input": "#e8630a",
    "Ethanol Input": "#d4a017",
    "Synthetic NG": "#e8905a",
    "Synthetic FT": "purple",
    "H2 Production": "lightgreen",
    "Demand": "bisque",
    "Transmission": "rosybrown",
}

category_names = {
    "Demand": "Demand",
    "Transmission": "T&D Losses",
    "H2 Production": "Electrolyzer",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Bioenergy Input": "Biofuel Prod.",
    "Sorbent DAC Input": "Sorbent DAC",
    "Ethylene Input": "Ethylene Sector",
    "Ethanol Input": "Ethanol Sector",
    "Hydro": "Hydro",
    "Nuclear": "Nuclear",
    "NG": "NG",
    "NG CCS": "NG CCS",
    "Solar": "Solar",
    "Wind": "Wind",
}


# ---------------------------------------------------------------------
# Plot MACRO-only electricity balance
# ---------------------------------------------------------------------

plot_df = macro_combined_data[desired_order].copy()

fig, ax = plt.subplots(figsize=(4.9, 3.0))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors[col] for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)

ax.set_ylabel("")
ax.set_title("Electricity Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-50, 50)
ax.set_xticks([-40, -20, 0, 20, 40])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

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

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.34)

plt.show()