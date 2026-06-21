#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir,
    dolphyn_results_folder, scenario_names,
)

dolphyn_scenario_paths = {
    "1": f'all_demand_test/{dolphyn_results_folder}',
}

macro_scenario_paths = {
    "1": f"6_15_168_restart_all_demand/results_001/results",
}

TONNE_TO_MT = 1e-6

# Liquid fuel end-use emission rates (tonne CO2 / MWh)
LIQUID_FUEL_EMISSION_RATES = {
    "Gasoline": 0.243968185,   # t-CO2/MWh Gasoline
    "JetFuel":  0.246356685,   # t-CO2/MWh JetFuel
    "Diesel":   0.249427613,   # t-CO2/MWh Diesel
}

# Natural gas end-use emission rate (tonne CO2 / MWh)
NG_EMISSION_RATE = 0.182890835  # t-CO2/MWh NG


# ---------------------------------------------------------------------
# Plot categories
# ---------------------------------------------------------------------

desired_order = [
    "Biomass Capture",
    "Ethanol Biomass Capture",
    "DAC Capture",
    "Conventional Liquid Fuels",
    "Conventional NG",
    "Synthetic Fuels and processes",
    "Synthetic NG and processes",
    "Bio NG and processes",
    "Biofuels and processes",
    "Ethylene and processes",
    "Ethanol and processes",
]

category_colors = {
    "Biomass Capture": "olivedrab",
    "Ethanol Biomass Capture": "#1a6e30",
    "DAC Capture": "darkblue",
    "Conventional Liquid Fuels": "grey",
    "Conventional NG": "lightgrey",
    "Synthetic Fuels and processes": "purple",
    "Synthetic NG and processes": "violet",
    "Bio NG and processes": "mediumseagreen",
    "Biofuels and processes": "lightgreen",
    "Ethylene and processes": "#e8630a",
    "Ethanol and processes": 'gold',
}

category_names = {
    "Biomass Capture": "Biomass",
    "Ethanol Biomass Capture": "Ethanol Biomass",
    "DAC Capture": "DAC",
    "Conventional Liquid Fuels": "Fossil Liquid Fuels",
    "Conventional NG": "Fossil NG",
    "Synthetic Fuels and processes": "Synthetic Liquid Fuels",
    "Synthetic NG and processes": "Synthetic NG",
    "Bio NG and processes": "Bio NG",
    "Biofuels and processes": "Biofuels",
    "Ethylene and processes": "Ethylene",
    "Ethanol and processes": "Ethanol",
}


# ---------------------------------------------------------------------
# Dolphyn CO2 emission balance
# ---------------------------------------------------------------------

dolphyn_columns_of_interest = [
    "Power Emissions",
    "H2 Emissions",
    "DAC Emissions",
    "Bio Elec Plant Emissions",
    "Biomass CO2 for Bio Elec",
    "Bio H2 Plant Emissions",
    "Biomass CO2 for Bio H2",
    "Bio LF Plant Emissions",
    "Biomass CO2 for Bio LF",
    "Bio NG Plant Emissions",
    "Biomass CO2 for Bio NG",
    "Conventional NG",
    "Syn NG Plant Emissions",
    "Synthetic NG",
    "Bio NG",
    "Conventional Gasoline",
    "Conventional Jetfuel",
    "Conventional Diesel",
    "Synfuel Plant Emissions",
    "Syn Gasoline",
    "Syn Jetfuel",
    "Syn Diesel",
    "Bio Gasoline",
    "Bio Jetfuel",
    "Bio Diesel",
    "NG Reduction from Power CCS",
    "NG Reduction from H2 CCS",
    "NG Reduction from DAC CCS",
    "Ethylene Production",
    "Bio Ethanol Plant Emissions",
    "Biomass CO2 for Bio Ethanol",
    "Ethylene Combustion",
]

dolphyn_combine_mapping = {
    "Power Emissions": "Conventional NG",
    "NG Reduction from Power CCS": "Conventional NG",

    "H2 Emissions": "Conventional NG",
    "NG Reduction from H2 CCS": "Conventional NG",

    "DAC Emissions": "DAC Capture",
    "NG Reduction from DAC CCS": "DAC Capture",

    "Biomass CO2 for Bio Elec": "Biomass Capture",
    "Biomass CO2 for Bio H2": "Biomass Capture",
    "Biomass CO2 for Bio LF": "Biomass Capture",
    "Biomass CO2 for Bio NG": "Biomass Capture",
    "Biomass CO2 for Bio Ethanol": "Ethanol Biomass Capture",

    "Bio Elec Plant Emissions": "Biofuels and processes",
    "Bio H2 Plant Emissions": "Biofuels and processes",
    "Bio LF Plant Emissions": "Biofuels and processes",
    "Bio NG Plant Emissions": "Bio NG and processes",
    "Bio NG": "Bio NG and processes",
    "Bio Gasoline": "Biofuels and processes",
    "Bio Jetfuel": "Biofuels and processes",
    "Bio Diesel": "Biofuels and processes",

    "Bio Ethanol Plant Emissions": "Ethanol and processes",

    "Syn NG Plant Emissions": "Synthetic NG and processes",
    "Synthetic NG": "Synthetic NG and processes",

    "Synfuel Plant Emissions": "Synthetic Fuels and processes",
    "Syn Gasoline": "Synthetic Fuels and processes",
    "Syn Jetfuel": "Synthetic Fuels and processes",
    "Syn Diesel": "Synthetic Fuels and processes",

    "Conventional Gasoline": "Conventional Liquid Fuels",
    "Conventional Jetfuel": "Conventional Liquid Fuels",
    "Conventional Diesel": "Conventional Liquid Fuels",

    "Ethylene Production": "Ethylene and processes",
    "Ethylene Combustion": "Ethylene and processes",
}

global_values_per_scenario = {}
annualsum_row_totals = {}

for scenario, scen_folder in dolphyn_scenario_paths.items():
    path = os.path.join(
        dolphyn_base_dir,
        scen_folder,
        "Results_CSC/Zone_CO2_emission_balance.csv",
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dolphyn CO2 emission balance file not found: {path}")

    df_raw = pd.read_csv(path, header=None)
    col_names = df_raw.iloc[0]
    zone_ids  = df_raw.iloc[1]

    annualsum_mask = df_raw.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)

    if annualsum_mask.any():
        annualsum_row = df_raw[annualsum_mask].iloc[0]

        non_global_col_names = set(
            col_names.iloc[i] for i in range(1, len(col_names))
            if str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')
        )

        zone_indices = [i for i in range(1, len(col_names))
                        if str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')]
        global_only_indices = [i for i in range(1, len(col_names))
                               if str(zone_ids.iloc[i]).strip() == 'Global'
                               and col_names.iloc[i] not in non_global_col_names]
        annualsum_row_totals[scenario] = sum(
            float(annualsum_row.iloc[i]) for i in zone_indices + global_only_indices
            if str(annualsum_row.iloc[i]).strip() not in ('', 'nan')
        ) * TONNE_TO_MT

        extracted = {}
        for col_name in dolphyn_columns_of_interest:
            zone_matches = [i for i in range(len(col_names))
                            if col_names.iloc[i] == col_name
                            and str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')]
            if zone_matches:
                extracted[col_name] = sum(float(annualsum_row.iloc[i]) for i in zone_matches) * TONNE_TO_MT
            else:
                global_matches = [i for i in range(len(col_names))
                                  if col_names.iloc[i] == col_name
                                  and str(zone_ids.iloc[i]).strip() == 'Global']
                extracted[col_name] = sum(float(annualsum_row.iloc[i]) for i in global_matches) * TONNE_TO_MT if global_matches else 0.0
        extracted_values = extracted
    else:
        extracted_values = {col: 0.0 for col in dolphyn_columns_of_interest}
        annualsum_row_totals[scenario] = 0.0

    global_values_per_scenario[scenario] = extracted_values

dolphyn_combined_data = pd.DataFrame(global_values_per_scenario).T
dolphyn_combined_data = dolphyn_combined_data.reindex(scenario_names).fillna(0.0)

dolphyn_combined_data = dolphyn_combined_data.rename(columns=dolphyn_combine_mapping)
dolphyn_combined_data = dolphyn_combined_data.T.groupby(level=0).sum().T

for col in desired_order:
    if col not in dolphyn_combined_data.columns:
        dolphyn_combined_data[col] = 0.0

dolphyn_combined_data = dolphyn_combined_data[desired_order]


# ---------------------------------------------------------------------
# Helper functions for MACRO
# ---------------------------------------------------------------------

def infer_liquid_fuel_commodity(row):
    """
    Infer liquid fuel commodity from Balance first, then Edge.
    """
    balance = str(row.get("Balance", "")).strip()
    edge = str(row.get("Edge", "")).strip().lower()

    if balance in ["Gasoline", "JetFuel", "Diesel"]:
        return balance

    if "gasoline" in edge:
        return "Gasoline"

    if "jetfuel" in edge or "jet_fuel" in edge or "jet" in edge:
        return "JetFuel"

    if "diesel" in edge:
        return "Diesel"

    return None


def map_macro_direct_co2_category(row):
    """
    Map MACRO annual_flows_balance_CO2.csv rows, excluding fuel end-use rows.

    Liquid fuel end-use and NG end-use emissions are reconstructed separately
    from the liquid fuels and NG balance files.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
    edge = str(row.get("Edge", "")).strip()

    edge_lower = edge.lower()

    # Ignore liquid fuel end-use CO2 rows.
    # These are reconstructed from annual_flows_balance_Liquid_Fuels.csv.
    if (
        sector == "Liquid fuels"
        and (
            "global_diesel_use" in edge_lower
            or "global_gasoline_use" in edge_lower
            or "global_jetfuel_use" in edge_lower
        )
    ):
        return None

    # Ignore NG end-use CO2 rows.
    # These are reconstructed from annual_flows_balance_NG.csv.
    if sector == "NG" and ("ng_end_use" in edge_lower or "natgas_end_use" in edge_lower):
        return None

    if sector == "CO2":
        return "DAC Capture"

    if sector == "Bioenergy":
        _BIO_NG_CATEGORIES = {"B-NG", "B-NG-CC40", "B-NG-CC99"}

        # Positive process emissions — route bio NG plant emissions separately.
        if any(s in edge_lower for s in ("co2_emission_edge", "co2_process_emission_edge", "co2_fuel_emission_edge")):
            if category in _BIO_NG_CATEGORIES:
                return "Bio NG and processes"
            return "Biofuels and processes"

        # Negative biogenic CO2 flows are the biomass capture term.
        if "co2_edge" in edge_lower:
            return "Biomass Capture"

        return None

    if sector == "Synthetic fuels":
        if "syn_ng" in edge_lower:
            return "Synthetic NG and processes"

        return "Synthetic Fuels and processes"

    if sector == "Power":
        return "Conventional NG"

    if sector == "Hydrogen":
        return "Conventional NG"

    # I will later have to ignore the end use thing here too
    if sector == "Ethylene":
        return "Ethylene and processes"

    # ethanol does not have an end use demand
    if sector == "Ethanol":
        if "co2_content_edge" in edge_lower:
            return "Ethanol Biomass Capture"
        if any(s in edge_lower for s in ("co2_emission_edge", "co2_process_emission_edge", "co2_fuel_emission_edge")):
            return "Ethanol and processes"
        return None

    return None


def map_macro_liquid_fuel_source(row):
    """
    Map liquid fuels balance rows to source categories for end-use emissions.
    """
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
    edge = str(row.get("Edge", "")).strip().lower()

    # Ignore demand/use rows from the liquid fuel balance.
    if "_use_" in edge or category in ["Diesel Use", "Gasoline Use", "Jetfuel Use"]:
        return None

    # Exclude primary-energy input edges (raw resource side); keep fuel output edges only.
    if "fossil_fuel_edge" in edge:
        return None

    if sector == "Bioenergy":
        return "Biofuels and processes"

    if sector == "Synthetic fuels":
        return "Synthetic Fuels and processes"

    if sector == "Liquid fuels" and category in ("Fossil Petroleum Refinery", "Fossil Liquid Fuels"):
        return "Conventional Liquid Fuels"

    if sector == "Ethylene":
        return "Ethylene and processes"

    return None

# ---------------------------------------------------------------------
# MACRO CO2 emission balance
# ---------------------------------------------------------------------

macro_rows = []

for scen_short, scen_path in macro_scenario_paths.items():

    macro_co2_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_CO2.csv",
    )

    macro_lf_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Liquid_Fuels.csv",
    )

    macro_ng_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_NG.csv",
    )

    liquid_fuel_emission_rates = LIQUID_FUEL_EMISSION_RATES
    ng_emission_rate = NG_EMISSION_RATE

    # -------------------------------------------------------------
    # 1. Direct CO2 balance rows, excluding fuel end-use rows
    # -------------------------------------------------------------

    if not os.path.exists(macro_co2_path):
        raise FileNotFoundError(f"MACRO CO2 balance file not found: {macro_co2_path}")

    macro_co2 = pd.read_csv(macro_co2_path)
    macro_co2.columns = macro_co2.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
    missing_cols = [c for c in required_cols if c not in macro_co2.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_co2_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_co2.columns.tolist()}"
        )

    macro_co2["Annual_Flow"] = (
        pd.to_numeric(macro_co2["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * TONNE_TO_MT
    )

    macro_co2["Plot_Category"] = macro_co2.apply(
        map_macro_direct_co2_category,
        axis=1,
    )

    macro_co2 = macro_co2[macro_co2["Plot_Category"].notna()].copy()

    direct_co2 = (
        macro_co2
        .groupby("Plot_Category")["Annual_Flow"]
        .sum()
    )

    for category, value in direct_co2.items():
        macro_rows.append(
            {
                "Scenario": scen_short,
                "Plot_Category": category,
                "Value": value,
                "Source": "Direct CO2 balance",
            }
        )

    # -------------------------------------------------------------
    # 2. Reconstruct liquid-fuel end-use emissions by fuel source
    # -------------------------------------------------------------

    if os.path.exists(macro_lf_path):
        macro_lf = pd.read_csv(macro_lf_path)
        macro_lf.columns = macro_lf.columns.str.strip()

        missing_cols = [c for c in required_cols if c not in macro_lf.columns]

        if missing_cols:
            raise ValueError(
                f"{macro_lf_path} is missing required columns: {missing_cols}. "
                f"Available columns are: {macro_lf.columns.tolist()}"
            )

        macro_lf["Annual_Flow"] = (
            pd.to_numeric(macro_lf["Annual_Flow"], errors="coerce")
            .fillna(0.0)
        )

        macro_lf["Plot_Category"] = macro_lf.apply(
            map_macro_liquid_fuel_source,
            axis=1,
        )

        macro_lf["Fuel_Commodity"] = macro_lf.apply(
            infer_liquid_fuel_commodity,
            axis=1,
        )

        macro_lf = macro_lf[
            macro_lf["Plot_Category"].notna()
            & macro_lf["Fuel_Commodity"].notna()
        ].copy()

        macro_lf["Emission_Rate"] = macro_lf["Fuel_Commodity"].map(
            liquid_fuel_emission_rates
        )

        if macro_lf["Emission_Rate"].isna().any():
            missing_fuels = sorted(
                macro_lf.loc[
                    macro_lf["Emission_Rate"].isna(),
                    "Fuel_Commodity",
                ].unique()
            )

            raise ValueError(
                "Missing liquid fuel emission rates for: "
                f"{missing_fuels}. Rates found: {liquid_fuel_emission_rates}"
            )

        macro_lf["End_Use_Emission_Mt"] = (
            macro_lf["Annual_Flow"].abs()
            * macro_lf["Emission_Rate"]
            * TONNE_TO_MT
        )

        lf_emissions = (
            macro_lf
            .groupby("Plot_Category")["End_Use_Emission_Mt"]
            .sum()
        )

        for category, value in lf_emissions.items():
            macro_rows.append(
                {
                    "Scenario": scen_short,
                    "Plot_Category": category,
                    "Value": value,
                    "Source": "Reconstructed liquid fuel end use",
                }
            )
    else:
        print(f"  Warning: no liquid fuels balance file for scenario {scen_short}, skipping liquid fuel emissions.")

    # -------------------------------------------------------------
    # 3. Reconstruct NG end-use emissions by fossil NG vs synthetic NG
    # -------------------------------------------------------------

    if not os.path.exists(macro_ng_path):
        raise FileNotFoundError(f"MACRO NG balance file not found: {macro_ng_path}")

    macro_ng = pd.read_csv(macro_ng_path)
    macro_ng.columns = macro_ng.columns.str.strip()

    missing_cols = [c for c in required_cols if c not in macro_ng.columns]

    if missing_cols:
        raise ValueError(
            f"{macro_ng_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_ng.columns.tolist()}"
        )

    macro_ng["Annual_Flow"] = (
        pd.to_numeric(macro_ng["Annual_Flow"], errors="coerce")
        .fillna(0.0)
    )

    edge_lower = macro_ng["Edge"].astype(str).str.lower()

    # Total NG end-use demand. These rows are usually negative in the balance file.
    # Match both "ng_end_use" and "natgas_end_use" naming conventions.
    is_ng_end_use = (
        edge_lower.str.contains("ng_end_use", na=False) |
        edge_lower.str.contains("natgas_end_use", na=False)
    )
    total_ng_end_use = -macro_ng.loc[is_ng_end_use, "Annual_Flow"].sum()

    # Synthetic NG production/supply. These rows are usually positive.
    is_syn_ng_supply = edge_lower.str.contains("syn_ng", na=False)
    syn_ng_supply = macro_ng.loc[is_syn_ng_supply, "Annual_Flow"].sum()

    # Bio NG production/supply (positive flows from Bioenergy sector, e.g. B-NG plants).
    is_bio_ng_supply = (
        (macro_ng["Sector"].str.strip() == "Bioenergy") &
        (macro_ng["Annual_Flow"] > 0)
    )
    bio_ng_supply = macro_ng.loc[is_bio_ng_supply, "Annual_Flow"].sum()

    # Ethylene CH4 co-production (positive flows from Ethylene sector, e.g. TSC+H2in:CH4).
    is_ethylene_ch4_supply = (
    (macro_ng["Sector"].str.strip() == "Ethylene") &
    edge_lower.str.contains("natgas_production_edge", na=False)
    )
    ethylene_ch4_supply = macro_ng.loc[is_ethylene_ch4_supply, "Annual_Flow"].sum()

    # Allocate supply sources to end-use in priority order: bio → syn → ethylene → fossil.
    bio_ng_end_use = min(max(bio_ng_supply, 0.0), max(total_ng_end_use, 0.0))
    remaining_after_bio = max(total_ng_end_use - bio_ng_end_use, 0.0)

    syn_ng_end_use = min(max(syn_ng_supply, 0.0), remaining_after_bio)
    remaining_after_syn = max(remaining_after_bio - syn_ng_end_use, 0.0)

    #fossil_ng_end_use = remaining_after_syn

    ethylene_ng_end_use = min(max(ethylene_ch4_supply, 0.0), remaining_after_syn)
    fossil_ng_end_use = max(remaining_after_syn - ethylene_ng_end_use, 0.0)

    bio_ng_emission_mt = bio_ng_end_use * ng_emission_rate * TONNE_TO_MT
    syn_ng_emission_mt = syn_ng_end_use * ng_emission_rate * TONNE_TO_MT
    ethylene_ng_emission_mt = ethylene_ng_end_use * ng_emission_rate * TONNE_TO_MT
    fossil_ng_emission_mt = fossil_ng_end_use * ng_emission_rate * TONNE_TO_MT

    print(f"\n  NG end-use breakdown for scenario: {scen_short}")
    print(f"    total_ng_end_use       = {total_ng_end_use:>14.2f} MWh")
    print(f"    bio_ng_supply          = {bio_ng_supply:>14.2f} MWh  -> bio_ng_end_use  = {bio_ng_end_use:>14.2f} MWh  ({bio_ng_emission_mt:.4f} Mt)")
    print(f"    syn_ng_supply          = {syn_ng_supply:>14.2f} MWh  -> syn_ng_end_use  = {syn_ng_end_use:>14.2f} MWh  ({syn_ng_emission_mt:.4f} Mt)")
    print(f"    ethylene_ch4_supply    = {ethylene_ch4_supply:>14.2f} MWh  -> ethylene_end_use= {ethylene_ng_end_use:>14.2f} MWh  ({ethylene_ng_emission_mt:.4f} Mt)")
    print(f"    fossil_ng_end_use      = {fossil_ng_end_use:>14.2f} MWh                                       ({fossil_ng_emission_mt:.4f} Mt)")
    print(f"    sum check (should = total_ng_end_use): {bio_ng_end_use + syn_ng_end_use + ethylene_ng_end_use + fossil_ng_end_use:.2f}")
    if total_ng_end_use > 0:
        print(f"    NG balance file rows matched as end-use: {is_ng_end_use.sum()}")
        print(f"    Bio NG supply rows (Bioenergy, +flow):  {is_bio_ng_supply.sum()}")
        print(f"    Syn NG supply rows (syn_ng edge):       {is_syn_ng_supply.sum()}")
        print(f"    Ethylene CH4 rows (Ethylene, +flow):    {is_ethylene_ch4_supply.sum()}")
    else:
        print("    WARNING: total_ng_end_use = 0 — check edge name patterns")
        all_edges = macro_ng["Edge"].astype(str).unique()
        print(f"    Total unique edge names in NG balance file: {len(all_edges)}")
        print(f"    All unique edge names:")
        for e in all_edges:
            print(f"      {e}")

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Bio NG and processes",
            "Value": bio_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Synthetic NG and processes",
            "Value": syn_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Ethylene and processes",
            "Value": ethylene_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Conventional NG",
            "Value": fossil_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )


macro_emissions_long = pd.DataFrame(macro_rows)

macro_combined_data = (
    macro_emissions_long
    .groupby(["Scenario", "Plot_Category"])["Value"]
    .sum()
    .unstack()
    .fillna(0.0)
    .reindex(scenario_names)
    .fillna(0.0)
)

for col in desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

macro_combined_data = macro_combined_data[desired_order]


# ---------------------------------------------------------------------
# Optional checks
# ---------------------------------------------------------------------

print("\nDolphyn CO2 emission balance by scenario (Mt):")
print(dolphyn_combined_data)

print("\nMACRO CO2 emission balance by scenario (Mt):")
print(macro_combined_data)

print("\nMACRO reconstructed emission components:")
print(
    macro_emissions_long
    .groupby(["Scenario", "Source", "Plot_Category"])["Value"]
    .sum()
    .reset_index()
)


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
# Plot Dolphyn and MACRO CO2 emission balance side by side
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
ax.set_title("CO2 Emission Balance (Mt)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(-1750, 1750)
ax.set_xticks([-1500, -750, 0, 750, 1500])
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

# Print balance summary
print()
for scenario in scenario_names:
    d_row = dolphyn_combined_data.loc[scenario]
    d_pos = d_row[d_row > 0].sum()
    d_neg = d_row[d_row < 0].sum()
    d_net = d_row.sum()
    row_total = annualsum_row_totals.get(scenario, float('nan'))
    print(f'Scenario: {scenario}')
    print(f'  Dolphyn AnnualSum row total : {row_total:+.2f} Mt')
    print(f'  Dolphyn plot net            : {d_net:+.2f} Mt  (pos: {d_pos:+.2f},  neg: {d_neg:+.2f})')
    m_row = macro_combined_data.loc[scenario]
    m_pos = m_row[m_row > 0].sum()
    m_neg = m_row[m_row < 0].sum()
    m_net = m_row.sum()
    print(f'  MACRO   plot net            : {m_net:+.2f} Mt  (pos: {m_pos:+.2f},  neg: {m_neg:+.2f})')
    print()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------
y_plotly_labels = [
    f"{scen} ({'D' if model == 'Dolphyn' else 'M'})"
    for scen, model in plot_df.index
]

fig_plotly = go.Figure()

for col in desired_order:
    display_name = category_names.get(col, col)
    color = category_colors.get(col, '#333333')
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=y_plotly_labels,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=color,
        hovertemplate='%{fullData.name}: %{x:.4f} Mt<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='CO2 Emission Balance (Mt)',
    xaxis_title='Mt CO2',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_emission_d_vs_m_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')