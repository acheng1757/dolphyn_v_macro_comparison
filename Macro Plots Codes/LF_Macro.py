import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

# flows.csv already has signs for consumption and production
# (-) means consumption pointing towards the asset
# (+) means production pointing away from the asset

# If there is both consumption AND production, then it will show as a net total in the plot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

# MACRO annual_flow values are treated as MWh.
macro_conversion_factor = 3.6e-9

# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Bio MeOH - Gasoline Non CCS",
    "Bio MeOH - Gasoline Mid CCS",
    "Bio MeOH - Gasoline High CCS",
    "Bio FT (High Jetfuel) High CCS",
    "Bio FT (High Diesel) Mid CCS",
    "Bio FT (High Diesel) High CCS",
    "SFT Non CCS",
    "SFT CCS",
    "Ethylene Gasoline",
    "Ethanol to Gasoline",
    "Ethanol to Diesel",
    "Ethanol to JetFuel",
    "Ethanol to Diesel JetFuel",
    "Fossil",
]

category_colors = {
    "Demand": "bisque",
    "Bio MeOH - Gasoline Non CCS": "lightblue",
    "Bio MeOH - Gasoline Mid CCS": "cornflowerblue",
    "Bio MeOH - Gasoline High CCS": "royalblue",
    "Bio FT (High Jetfuel) High CCS": "chocolate",
    "Bio FT (High Diesel) Mid CCS": "limegreen",
    "Bio FT (High Diesel) High CCS": "forestgreen",
    "SFT Non CCS": "purple",
    "SFT CCS": "indigo",
    "Ethylene Gasoline": "#e8630a",
    "Ethanol to Gasoline":      "#ffd700",
    "Ethanol to Diesel":        "#daa520",
    "Ethanol to JetFuel":       "#b8860b",
    "Ethanol to Diesel JetFuel": "#cd853f",
    "Fossil": "grey",
}

label_map = {
    "Demand": "Demand",
    "Bio MeOH - Gasoline Non CCS": "Bio-MTG",
    "Bio MeOH - Gasoline Mid CCS": "Bio-MTG CC31",
    "Bio MeOH - Gasoline High CCS": "Bio-MTG CC99",
    "Bio FT (High Jetfuel) High CCS": "Bio-FT (Jet) CC84",
    "Bio FT (High Diesel) Mid CCS": "Bio-FT (Diesel) CC53",
    "Bio FT (High Diesel) High CCS": "Bio-FT (Diesel) CC99",
    "SFT Non CCS": "Syn-FT (Jet)",
    "SFT CCS": "Syn-FT (Jet) CC99",
    "Ethylene Gasoline": "Ethylene Naphtha",
    "Ethanol to Gasoline":      "Eth. Upgrading (Gasoline)",
    "Ethanol to Diesel":        "Eth. Upgrading (Diesel)",
    "Ethanol to JetFuel":       "Eth. Upgrading (JetFuel)",
    "Ethanol to Diesel JetFuel": "Eth. Upgrading (Diesel+Jet)",
    "Fossil": "Fossil Liquids",
}


# ---------------------------------------------------------------------
# MACRO liquid-fuel balance helpers
# ---------------------------------------------------------------------

def find_macro_lf_balance_file(results_dir):
    """
    Try likely liquid-fuels balance file names.
    """
    balance_dir = os.path.join(
        results_dir,
        "annual_flow_results",
        "balance_specific_flows",
    )

    candidate_files = [
        "annual_flows_balance_Liquid_Fuels.csv",
        "annual_flows_balance_Liquid_Fuel.csv",
        "annual_flows_balance_LF.csv",
        "annual_flows_balance_Liquid fuels.csv",
        "annual_flows_balance_Liquid_Fuels_Balance.csv",
        "annual_flows_balance_LiquidFuel.csv",
    ]

    for filename in candidate_files:
        path = os.path.join(balance_dir, filename)
        if os.path.exists(path):
            return path

    if os.path.exists(balance_dir):
        for filename in os.listdir(balance_dir):
            filename_lower = filename.lower()

            if (
                filename_lower.endswith(".csv")
                and "annual_flows_balance" in filename_lower
                and (
                    "liquid" in filename_lower
                    or "lf" in filename_lower
                    or "fuel" in filename_lower
                )
            ):
                return os.path.join(balance_dir, filename)

    return None


def map_macro_lf_category(row):
    """
    Map MACRO liquid-fuels balance rows to plotting categories.

    Demand rows are excluded.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
    edge = str(row.get("Edge", "")).strip()

    sector_lower = sector.lower()
    category_lower = category.lower()
    edge_lower = edge.lower()

    text = f"{sector_lower} {category_lower} {edge_lower}"

    # Demand rows
    if sector == "Demand" or "demand" in text:
        return "Demand"

    # Synthetic liquid fuels
    if sector == "Synthetic fuels" or "synthetic" in sector_lower:
        if "wccs" in text or "ccs" in text or "cc99" in text:
            return "SFT CCS"

        if (
            "s-j" in text
            or "synfuel" in text
            or "synthetic" in text
            or "ft" in text
        ):
            return "SFT Non CCS"

        return None

    # Bioenergy liquid fuels
    if sector == "Bioenergy" or "bio" in sector_lower:
        if "gasification_ccs_99" in text or ("gasification" in text and "99" in text):
            return "Bio MeOH - Gasoline High CCS"

        if "gasification_ccs_31" in text or ("gasification" in text and "31" in text):
            return "Bio MeOH - Gasoline Mid CCS"

        if "gasification_non_ccs" in text or ("gasification" in text and "non" in text):
            return "Bio MeOH - Gasoline Non CCS"

        if "high_diesel_ccs_99" in text or ("high_diesel" in text and "99" in text):
            return "Bio FT (High Diesel) High CCS"

        if "high_diesel_ccs_53" in text or ("high_diesel" in text and "53" in text):
            return "Bio FT (High Diesel) Mid CCS"

        # Not included in desired_order, following your reference plot.
        if "high_diesel_non_ccs" in text or ("high_diesel" in text and "non" in text):
            return None

        if "high_jetfuel" in text:
            return "Bio FT (High Jetfuel) High CCS"

        return None

    # Exclude crude-oil input edges (negative resource consumption, not liquid fuel supply)
    if category == "Fossil Liquid Fuels":
        return None

    # Fossil liquid fuels
    if (
        "fossil" in text
        or "petroleum" in text
        or "refinery" in text
        or "oil" in text
    ):
        return "Fossil"

    if sector == "Ethylene":
        return "Ethylene Gasoline"

    return None

# ---------------------------------------------------------------------
# Read MACRO liquid-fuel balance
# ---------------------------------------------------------------------

macro_lf_tables = []

for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    macro_lf_path = find_macro_lf_balance_file(results_dir)

    if macro_lf_path is None:
        print(
            "Warning: MACRO liquid-fuels balance file not found for "
            f"{scen_short} in {results_dir}"
        )
        continue

    macro_lf = pd.read_csv(macro_lf_path)
    macro_lf.columns = macro_lf.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_lf.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_lf_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_lf.columns.tolist()}"
        )

    macro_lf["Scenario"] = scen_short

    macro_lf["Annual_Flow"] = (
        pd.to_numeric(macro_lf["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * macro_conversion_factor
    )

    macro_lf["Plot_Category"] = macro_lf.apply(
        map_macro_lf_category,
        axis=1,
    )

    # Exclude demand and unmapped rows
    macro_lf = macro_lf[macro_lf["Plot_Category"].notna()].copy()

    macro_lf_tables.append(macro_lf)


if macro_lf_tables:
    macro_lf_combined = pd.concat(macro_lf_tables, ignore_index=True)

    macro_combined_data = (
        macro_lf_combined
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
# Add Ethanol_to_X LF production split by process
# ---------------------------------------------------------------------
# Ethanol_to_X assets are tagged as "Transmission" in Step 1, so they
# are absent from the Liquid_Fuels balance file.  We pull their LF
# output edges from the all_nonzero file, one category per process.
# Diesel_JetFuel must be matched before plain Diesel to avoid overlap.

_LF_PROD_EDGES = (
    "gasoline_production_edge",
    "diesel_production_edge",
    "jetfuel_production_edge",
)

# (plot_category, asset_substring, exclude_substring_or_None)
_ETHANOL_UPGRADING_ASSETS = [
    ("Ethanol to Gasoline",      "_Ethanol_to_Gasoline_",      None),
    ("Ethanol to Diesel JetFuel", "_Ethanol_to_Diesel_JetFuel_", None),
    ("Ethanol to Diesel",        "_Ethanol_to_Diesel_",        "_Ethanol_to_Diesel_JetFuel_"),
    ("Ethanol to JetFuel",       "_Ethanol_to_JetFuel_",       None),
]


def _load_ethanol_upgrading_by_process(results_dir):
    """Return {plot_category: annual_flow_MWh} for each Ethanol_to_X process."""
    path = os.path.join(
        results_dir,
        "annual_flow_results",
        "all_nonzero_annual_flows_with_categories.csv",
    )
    result = {cat: 0.0 for cat, _, _ in _ETHANOL_UPGRADING_ASSETS}
    if not os.path.exists(path):
        return result
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    if "Edge" not in df.columns or "Annual_Flow" not in df.columns:
        return result
    flows = pd.to_numeric(df["Annual_Flow"], errors="coerce").fillna(0.0)
    for cat, include, exclude in _ETHANOL_UPGRADING_ASSETS:
        mask = (
            df["Edge"].str.contains(include, na=False) &
            df["Edge"].str.endswith(_LF_PROD_EDGES)
        )
        if exclude is not None:
            mask &= ~df["Edge"].str.contains(exclude, na=False)
        result[cat] = flows[mask].sum()
    return result


for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    process_flows = _load_ethanol_upgrading_by_process(results_dir)
    for cat, raw_flow in process_flows.items():
        if cat not in macro_combined_data.columns:
            macro_combined_data[cat] = 0.0
        if scen_short in macro_combined_data.index:
            macro_combined_data.loc[scen_short, cat] = raw_flow * macro_conversion_factor


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

print("\nMACRO liquid fuels production by scenario (EJ), demand excluded:")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Liquid Fuels balance check:")
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
# Plot MACRO-only liquid-fuels production
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

fig, ax = plt.subplots(figsize=(5.2, 3.2))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors.get(col, "#333333") for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)

ax.set_ylabel("")
ax.set_title("Total LF Prod. (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-14, 14)
ax.set_xticks([-12, -8, -4, 0, 4, 8, 12])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
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