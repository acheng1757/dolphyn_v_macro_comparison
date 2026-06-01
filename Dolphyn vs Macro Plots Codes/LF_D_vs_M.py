import os
import pandas as pd
import matplotlib.pyplot as plt
import sys

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
    scenario_names[0]: f"all_demand_test/{dolphyn_results_folder}",
}

macro_scenario_paths = {
    scenario_names[0]: f"clean_slate_5_25/{macro_results_folder}/results",
}

_scen_folder = dolphyn_scenario_paths[scenario_names[0]]

bf_results_files = [
    os.path.join(dolphyn_base_dir, _scen_folder, "Results_BESC/BESC_Bio_LF_capacity.csv"),
]

sf_results_files = [
    os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/Synfuel_capacity.csv"),
]

fuels_balance_files = {
    "Gasoline": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Gasoline_balance.csv"),
    ],
    "Jetfuel": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Jetfuel_balance.csv"),
    ],
    "Diesel": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Diesel_balance.csv"),
    ],
}

# Exact Dolphyn conversion factor from your reference script:
# MMBtu -> MWh -> EJ
conversion_factor = 0.293071 * 3.6e-9

# MACRO annual_flow values were treated as MWh in your previous plots.
macro_conversion_factor = 3.6e-9


# ---------------------------------------------------------------------
# Dolphyn liquid-fuel balance: same calculations as your reference script
# ---------------------------------------------------------------------

def load_bf_results(files, scenario_names):
    dfs = []

    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df["Scenario"] = scenario

        df["Total_Biofuel_Production"] = (
            df["Annual_Biogasoline_Production"] +
            df["Annual_Biojetfuel_Production"] +
            df["Annual_Biodiesel_Production"]
        ) * conversion_factor

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def categorize_bf_resource(resource):
    if "Gasification_CCS_99" in resource:
        return "Bio MeOH - Gasoline High CCS"
    elif "Gasification_CCS_31" in resource:
        return "Bio MeOH - Gasoline Mid CCS"
    elif "Gasification_Non_CCS" in resource:
        return "Bio MeOH - Gasoline Non CCS"
    elif "High_Diesel_CCS_99" in resource:
        return "Bio FT (High Diesel) High CCS"
    elif "High_Diesel_CCS_53" in resource:
        return "Bio FT (High Diesel) Mid CCS"
    elif "High_Diesel_Non_CCS" in resource:
        return "Bio FT (High Diesel) Non CCS"
    elif "High_Jetfuel" in resource:
        return "Bio FT (High Jetfuel) High CCS"


def load_sf_results(files, scenario_names):
    dfs = []

    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df["Scenario"] = scenario

        df["Total_Synfuel_Production"] = (
            df["Annual_Syngasoline_Production"] +
            df["Annual_Synjetfuel_Production"] +
            df["Annual_Syndiesel_Production"]
        ) * conversion_factor

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def categorize_sf_resource(resource):
    if "Synfuel_Plant" in resource and "CCS" not in resource:
        return "SFT Non CCS"
    elif "Synfuel_Plant_wCCS" in resource:
        return "SFT CCS"


def load_fossil_fuel_balances(files, scenario_names):
    dfs = []

    for fuel_type, file_list in files.items():
        for file, scenario in zip(file_list, scenario_names):
            df = pd.read_csv(file)
            df["Scenario"] = scenario

            demand_value = (
                pd.to_numeric(df.iloc[1, -2], errors="coerce")
                * conversion_factor
            )

            fossil_value = (
                pd.to_numeric(df.iloc[1, -3], errors="coerce")
                * conversion_factor
            )

            df_result = pd.DataFrame({
                "Scenario": [scenario],
                "Fossil": [fossil_value],
            })

            dfs.append(df_result)

    return pd.concat(dfs, ignore_index=True)


# Load biofuel results and categorize
bf_data = load_bf_results(bf_results_files, scenario_names)
bf_data["Resource_Category"] = bf_data["Resource"].apply(categorize_bf_resource)

bf_aggregated = (
    bf_data
    .groupby(["Scenario", "Resource_Category"])["Total_Biofuel_Production"]
    .sum()
    .unstack()
    .fillna(0)
)

# Load synfuel results and categorize
sf_data = load_sf_results(sf_results_files, scenario_names)
sf_data["Resource_Category"] = sf_data["Resource"].apply(categorize_sf_resource)

sf_aggregated = (
    sf_data
    .groupby(["Scenario", "Resource_Category"])["Total_Synfuel_Production"]
    .sum()
    .unstack()
    .fillna(0)
)

# Load fossil fuel results and categorize
fossil_data = load_fossil_fuel_balances(fuels_balance_files, scenario_names)
fossil_aggregated = fossil_data.groupby("Scenario")[["Fossil"]].sum()

# Combine all Dolphyn data exactly as in your reference script
dolphyn_combined_data = bf_aggregated.join(
    fossil_aggregated,
    on="Scenario",
    how="left",
).fillna(0)

dolphyn_combined_data = sf_aggregated.join(
    dolphyn_combined_data,
    on="Scenario",
    how="left",
).fillna(0)

dolphyn_combined_data = dolphyn_combined_data.reindex(scenario_names).fillna(0)


# ---------------------------------------------------------------------
# Desired order, colors, and labels exactly from your reference script
# ---------------------------------------------------------------------

desired_order = [
    "Bio MeOH - Gasoline Non CCS",
    "Bio MeOH - Gasoline Mid CCS",
    "Bio MeOH - Gasoline High CCS",
    "Bio FT (High Jetfuel) High CCS",
    "Bio FT (High Diesel) Mid CCS",
    "Bio FT (High Diesel) High CCS",
    "SFT Non CCS",
    "SFT CCS",
    "Ethylene Gasoline",
    "Fossil",
]

# Reorder the Dolphyn columns exactly as your reference script does:
# only keep columns that exist.
dolphyn_combined_data = dolphyn_combined_data[
    [col for col in desired_order if col in dolphyn_combined_data.columns]
]

category_colors = {
    "Bio MeOH - Gasoline Non CCS": "lightblue",
    "Bio MeOH - Gasoline Mid CCS": "cornflowerblue",
    "Bio MeOH - Gasoline High CCS": "royalblue",
    "Bio FT (High Jetfuel) High CCS": "chocolate",
    "Bio FT (High Diesel) Mid CCS": "limegreen",
    "Bio FT (High Diesel) High CCS": "forestgreen",
    "SFT Non CCS": "purple",
    "SFT CCS": "indigo",
    "Ethylene Gasoline": "#e8630a",
    "Fossil": "grey",
}

label_map = {
    "Bio MeOH - Gasoline Non CCS": "Bio-MTG",
    "Bio MeOH - Gasoline Mid CCS": "Bio-MTG CC31",
    "Bio MeOH - Gasoline High CCS": "Bio-MTG CC99",
    "Bio FT (High Jetfuel) High CCS": "Bio-FT (Jet) CC84",
    "Bio FT (High Diesel) Mid CCS": "Bio-FT (Diesel) CC53",
    "Bio FT (High Diesel) High CCS": "Bio-FT (Diesel) CC99",
    "SFT Non CCS": "Syn-FT (Jet)",
    "SFT CCS": "Syn-FT (Jet) CC99",
    "Ethylene Gasoline": "Ethylene Gasoline",
    "Fossil": "Fossil Liquids",
}


# ---------------------------------------------------------------------
# MACRO liquid-fuel balance
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
    Map MACRO LF balance rows to the exact same plotting categories
    used on the Dolphyn side.

    Demand rows are intentionally excluded.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
    edge = str(row.get("Edge", "")).strip()

    sector_lower = sector.lower()
    category_lower = category.lower()
    edge_lower = edge.lower()

    text = f"{sector_lower} {category_lower} {edge_lower}"

    # Exclude demand rows from MACRO LF plot
    if sector == "Demand" or "demand" in text:
        return None

    # Synthetic liquid fuels
    if sector == "Synthetic fuels" or "synthetic" in sector_lower:
        if "wccs" in text or "ccs" in text or "cc99" in text:
            return "SFT CCS"

        if "s-j" in text or "synfuel" in text or "synthetic" in text or "ft" in text:
            return "SFT Non CCS"

        return None

    # Bioenergy liquid fuels
    if sector == "Bioenergy" or "bio" in sector_lower:
        # Match same categories as the Dolphyn script.
        if "gasification_ccs_99" in text or "gasification" in text and "99" in text:
            return "Bio MeOH - Gasoline High CCS"

        if "gasification_ccs_31" in text or "gasification" in text and "31" in text:
            return "Bio MeOH - Gasoline Mid CCS"

        if "gasification_non_ccs" in text or "gasification" in text and "non" in text:
            return "Bio MeOH - Gasoline Non CCS"

        if "high_diesel_ccs_99" in text or "high_diesel" in text and "99" in text:
            return "Bio FT (High Diesel) High CCS"

        if "high_diesel_ccs_53" in text or "high_diesel" in text and "53" in text:
            return "Bio FT (High Diesel) Mid CCS"

        # This is intentionally not included in desired_order, following your reference plot.
        # If you want it later, add it to desired_order/colors/labels.
        if "high_diesel_non_ccs" in text or "high_diesel" in text and "non" in text:
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
# Align Dolphyn and MACRO columns for paired plot
# ---------------------------------------------------------------------

full_desired_order = [
    col for col in desired_order
    if col in dolphyn_combined_data.columns
]

for col in full_desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [full_desired_order]
)

dolphyn_combined_data = (
    dolphyn_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [full_desired_order]
)


print("\nDolphyn liquid fuels production by scenario (EJ):")
print(dolphyn_combined_data)

print("\nMACRO liquid fuels production by scenario (EJ), demand excluded:")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Build paired plotting table
# ---------------------------------------------------------------------

plot_rows = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(dolphyn_combined_data.loc[scen, full_desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, full_desired_order])
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
# Plot Dolphyn and MACRO side by side
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.2, 4.4))

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
    color=[category_colors.get(col, "#333333") for col in full_desired_order],
)

# Move bars from default positions 0, 1, 2, ... to custom positions with gaps
for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Total LF Prod. (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(0, 13)
ax.set_xticks([0, 4, 8, 12])
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

# Custom legend using the same labels as your reference plot
handles, _ = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in full_desired_order]

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