import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_results_folder

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

MWH_TO_EJ = 3.6e-9
conversion_factor = MWH_TO_EJ

macro_scenario_paths = {
    "clean_slate_5_25": f"clean_slate_5_25/{macro_results_folder}/results",
}


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def map_macro_h2_category(row):
    """
    Map MACRO annual_flows_balance_H2.csv rows to H2-balance
    plotting categories.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Demand rows
    if sector == "Demand":
        return "Demand"

    # H2 production technologies
    if sector == "Hydrogen":
        category_lower = category.lower()

        if "electrolyzer" in category_lower:
            return "Electrolyzer"

        if category in ["NG CCS H2", "NG CCS"]:
            return "NG CCS H2"

        if "ccs" in category_lower and (
            "ng" in category_lower or "natural" in category_lower
        ):
            return "NG CCS H2"

        if "bio" in category_lower or "beccs" in category_lower:
            return "BECCS H2"

        # Exclude H2 storage / compressor / other internal flows
        if (
            "stor" in category_lower
            or "storage" in category_lower
            or "comp" in category_lower
        ):
            return None

        return None

    # Synthetic-fuel H2 consumption
    if sector == "Synthetic fuels":
        if category == "S-NG":
            return "Synthetic NG"

        if category in ["S-J", "S-J-CC99", "S-J-99"]:
            return "Synthetic FT"

        category_lower = category.lower()

        if "ng" in category_lower:
            return "Synthetic NG"

        if (
            "s-j" in category_lower
            or "jet" in category_lower
            or "ft" in category_lower
        ):
            return "Synthetic FT"

        return None

    # Bioenergy H2 production if represented outside Hydrogen sector
    if sector == "Bioenergy":
        category_lower = category.lower()

        if (
            "h2" in category_lower
            or "hydrogen" in category_lower
            or "bio" in category_lower
        ):
            return "BECCS H2"

        return None

    if sector == "Ethylene":
        return "Ethylene Sector"

    return None


# ---------------------------------------------------------------------
# Read MACRO H2 balance from annual_flows_balance_H2.csv
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Synthetic FT",
    "Synthetic NG",
    "Ethylene Sector",
    "Electrolyzer",
    "NG CCS H2",
    "BECCS H2",
]

macro_h2_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    macro_h2_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_H2.csv",
    )

    if not os.path.exists(macro_h2_path):
        print(f"Warning: MACRO H2 balance file not found: {macro_h2_path}")
        continue

    macro_h2 = pd.read_csv(macro_h2_path)
    macro_h2.columns = macro_h2.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_h2.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_h2_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_h2.columns.tolist()}"
        )

    macro_h2["Scenario"] = scen_short

    # Convert MWh to EJ
    macro_h2["Annual_Flow"] = (
        pd.to_numeric(macro_h2["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * conversion_factor
    )

    macro_h2["Plot_Category"] = macro_h2.apply(
        map_macro_h2_category,
        axis=1,
    )

    macro_h2 = macro_h2[macro_h2["Plot_Category"].notna()].copy()

    macro_h2_tables.append(macro_h2)


if macro_h2_tables:
    macro_h2_combined = pd.concat(macro_h2_tables, ignore_index=True)

    macro_combined_data = (
        macro_h2_combined
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

print("\nMACRO H2 balance by scenario (EJ):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Hydrogen balance check:")
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
    "Electrolyzer": "lightgreen",
    "NG CCS H2": "deepskyblue",
    "BECCS H2": "seagreen",
    "Synthetic FT": "purple",
    "Synthetic NG": "violet",
    "Ethylene Sector": "#e8630a",
    "Demand": "bisque",
}

category_names = {
    "Electrolyzer": "Electrolyzer",
    "NG CCS H2": "NG CCS",
    "BECCS H2": "BECCS H2",
    "Synthetic FT": "Syn. Liquids",
    "Synthetic NG": "Syn. NG",
    "Ethylene Sector": "Ethylene Sector",
    "Demand": "Demand",
}


# ---------------------------------------------------------------------
# Plot MACRO-only H2 balance
# ---------------------------------------------------------------------

plot_df = macro_combined_data[desired_order].copy()

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
ax.set_title("H2 Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-18, 18)
ax.set_xticks([-16, -8, 0, 8, 16])
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