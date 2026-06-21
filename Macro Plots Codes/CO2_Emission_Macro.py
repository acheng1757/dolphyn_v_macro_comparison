#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_input_paths, macro_scenario_paths, carbon_end_use_dict, get_demand_path_for_scenario

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

# Used to locate asset json files.
# This assumes assets/ is directly under each Macro scenario input folder:
# Macro/NineZones_High_Biomass_High_CO2/assets/...

TONNE_TO_MT = 1e-6

# ---------------------------------------------------------------------
# Plot categories
# ---------------------------------------------------------------------

desired_order = [
    "Biomass Capture",
    "Ethanol Biomass Capture",
    "DAC Capture",
    "Conventional Liquid Fuels",
    "Conventional NG",
    "NG End Use",
    "Synthetic Fuels and processes",
    "Synthetic Fuels Combustion",
    "Synthetic NG and processes",
    "Synthetic NG End Use",
    "Bio NG End Use",
    "Ethylene NG End Use",
    "Biofuels and processes",
    "Biofuels Combustion",
    "Ethylene and processes",
    "Ethanol and processes",
    "Ethanol Combustion",
    "Ethanol LF Combustion",
]

category_colors = {
    "Biomass Capture": "olivedrab",
    "Ethanol Biomass Capture": "#1a6e30",
    "DAC Capture": "darkblue",
    "Conventional Liquid Fuels": "grey",
    "Conventional NG": "#c0504d",
    "NG End Use": "#d87878",
    "Synthetic Fuels and processes": "purple",
    "Synthetic Fuels Combustion": "#c890d0",
    "Synthetic NG and processes": "#e8905a",
    "Synthetic NG End Use": "#f0b898",
    "Bio NG End Use": "#a8c97f",
    "Ethylene NG End Use": "#f2a679",
    "Biofuels and processes": "seagreen",
    "Biofuels Combustion": "#90c8a0",
    "Ethylene and processes": "#e8630a",
    "Ethanol and processes": "#d4a017",
    "Ethanol Combustion": "#f0cc6a",
    "Ethanol LF Combustion": "#c8b040",
}

category_names = {
    "Biomass Capture": " Non-Ethanol Biomass",
    "Ethanol Biomass Capture": "Ethanol Biomass",
    "DAC Capture": "DAC",
    "Conventional Liquid Fuels": "Fossil Liquid Fuels",
    "Conventional NG": "Fossil NG Process",
    "NG End Use": "Fossil NG End Use",
    "Synthetic Fuels and processes": "Syn. Liquids Process",
    "Synthetic Fuels Combustion": "Syn. Liquids Combustion",
    "Synthetic NG and processes": "Syn. NG Process",
    "Synthetic NG End Use": "Syn. NG End Use",
    "Bio NG End Use": "Bio NG End Use",
    "Ethylene NG End Use": "Ethylene NG End Use",
    "Biofuels and processes": "Bio Process",
    "Biofuels Combustion": "Biofuels Combustion",
    "Ethylene and processes": "Ethylene",
    "Ethanol and processes": "Ethanol Process",
    "Ethanol Combustion": "Ethanol Combustion",
    "Ethanol LF Combustion": "Ethanol LF Combustion",
}


# ---------------------------------------------------------------------
# Helper functions for MACRO
# ---------------------------------------------------------------------

def find_macro_asset_path(scen_short, filename):
    """
    Try to locate an asset JSON file for a MACRO scenario.
    """
    candidate_paths = [
        os.path.join(
            macro_base_dir,
            macro_input_paths[scen_short],
            "assets",
            filename,
        ),
        os.path.join(
            macro_base_dir,
            "assets",
            filename,
        ),
    ]

    for path in candidate_paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        f"Could not find {filename} for scenario {scen_short}. Checked:\n  "
        + "\n  ".join(candidate_paths)
    )



def read_ng_emission_rate(json_path):
    """
    Read natural gas end-use emission rate from naturalgas_end_use.json.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    for block in data.get("NaturalGasEndUse", []):
        global_data = block.get("global_data", {})

        if "emission_rate" in global_data:
            return float(global_data["emission_rate"])

    raise ValueError(f"Could not find emission_rate in {json_path}")


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
    if sector == "NG" and "ng_end_use" in edge_lower:
        return None

    if sector == "CO2":
        return "DAC Capture"

    if sector == "Bioenergy":
        # Positive process emissions are added to biofuels/processes.
        if any(s in edge_lower for s in ("co2_emission_edge", "co2_process_emission_edge", "co2_fuel_emission_edge")):
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

    if sector == "Ethylene":
        return "Ethylene and processes"

    if sector == "Ethanol":
        if "co2_content_edge" in edge_lower:
            return "Ethanol Biomass Capture"
        if any(s in edge_lower for s in ("co2_emission_edge", "co2_process_emission_edge", "co2_fuel_emission_edge")):
            return "Ethanol and processes"
        return None

    return None


def read_ethanol_emission_rate(json_path):
    """
    Read ethanol end-use emission rate from ethanol_end_use.json.

    The file uses a GasolineEndUse (or similar) wrapper with the rate
    nested under instance_data[*].transforms.emission_rate.  All
    instances share the same rate, so the first non-None value is returned.
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    for blocks in data.values():
        for block in blocks:
            for item in block.get("instance_data", []):
                rate = item.get("transforms", {}).get("emission_rate")
                if rate is not None:
                    return float(rate)

    raise ValueError(f"Could not find emission_rate in {json_path}")


def map_macro_ethanol_source(row):
    """
    Map ethanol balance demand rows to source categories for end-use emissions.

    Only the direct end-use demand (Demand sector) is used; production
    supply rows and upgrading consumption rows are excluded.  The model
    does not emit a separate CO2 edge for direct ethanol combustion
    (biogenic carbon-neutral treatment), so this reconstruction is kept
    strictly to the demand volume × emission rate.
    """
    sector = str(row.get("Sector", "")).strip()

    if sector == "Demand":
        return "Ethanol Combustion"

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

    if sector == "Bioenergy":
        return "Biofuels Combustion"

    if sector == "Synthetic fuels":
        return "Synthetic Fuels Combustion"

    if sector == "Liquid fuels" and category == "Fossil Petroleum Refinery":
        return "Conventional Liquid Fuels"

    if sector == "Ethylene":
        return "Ethylene and processes"

    # Ethanol_to_X upgrading assets sit in the Transmission sector;
    # Step 1 now assigns them Gasoline/Diesel/Jetfuel Balances so they
    # land in the Liquid_Fuels file — attribute their combustion here.
    if sector == "Transmission":
        return "Ethanol LF Combustion"

    return None


# ---------------------------------------------------------------------
# MACRO CO2 emission balance
# ---------------------------------------------------------------------

macro_rows = []
scenarios_without_ethanol_end_use = []
lf_co2_actual_by_scen = {}
ng_total_emission_by_scen = {}
ethanol_emission_by_scen = {}
demand_path_by_scen = {}
lf_fossil_checker_rows = []
ng_balance_checker_rows = []
ng_production_share_rows = []

required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]

for scen_short, scen_path in macro_scenario_paths.items():
    demand_path_by_scen[scen_short] = get_demand_path_for_scenario(scen_path)

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

    ng_json_path = find_macro_asset_path(
        scen_short,
        "naturalgas_end_use.json",
    )

    ng_emission_rate = read_ng_emission_rate(ng_json_path)

    # -------------------------------------------------------------
    # 1. Direct CO2 balance rows, excluding fuel end-use rows
    # -------------------------------------------------------------

    if not os.path.exists(macro_co2_path):
        raise FileNotFoundError(f"MACRO CO2 balance file not found: {macro_co2_path}")

    macro_co2 = pd.read_csv(macro_co2_path)
    macro_co2.columns = macro_co2.columns.str.strip()

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

    # Capture actual LF CO2 per fuel type (in Mt) before those rows are excluded.
    # This avoids relying on JSON emission rates, which may differ from what the
    # model computed internally (e.g. gasoline CO2 uses rate=1.0 in some scenarios).
    lf_co2_actual = {}
    for _, r in macro_co2[macro_co2["Sector"] == "Liquid fuels"].iterrows():
        e = r["Edge"].lower()
        if "global_gasoline_use" in e:
            lf_co2_actual["Gasoline"] = lf_co2_actual.get("Gasoline", 0) + r["Annual_Flow"]
        elif "global_diesel_use" in e:
            lf_co2_actual["Diesel"] = lf_co2_actual.get("Diesel", 0) + r["Annual_Flow"]
        elif "global_jetfuel_use" in e:
            lf_co2_actual["JetFuel"] = lf_co2_actual.get("JetFuel", 0) + r["Annual_Flow"]

    lf_co2_actual_by_scen[scen_short] = dict(lf_co2_actual)

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
    #
    # Uses the actual CO2 values from the CO2 balance file (captured
    # above in lf_co2_actual) and distributes them proportionally to
    # each supply source based on volume fractions relative to total
    # fuel DEMAND (not tracked supply).
    #
    # The LF balance file does not fully capture fossil refinery supply
    # when it operates as the residual supplier — e.g. in a scenario
    # without Ethanol_to_Gasoline, the refinery may supply 5.3 EJ of
    # gasoline but only ~1.6 EJ appears in the balance file.  Using
    # demand as the denominator and computing fossil as
    # (demand − tracked non-fossil supply) corrects this.
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
        macro_lf["Fuel_Commodity"] = macro_lf.apply(infer_liquid_fuel_commodity, axis=1)

        # ── 2a. Total demand per fuel from the Use category rows ──────────
        # Category "Gasoline Use" / "Diesel Use" / "Jetfuel Use" rows hold
        # the single authoritative demand volume for each fuel type.
        _CAT_TO_FUEL = {
            "Gasoline Use": "Gasoline",
            "Diesel Use":   "Diesel",
            "Jetfuel Use":  "JetFuel",
        }
        demand_vol_by_fuel = {}
        for _, r in macro_lf.iterrows():
            fuel = _CAT_TO_FUEL.get(str(r.get("Category", "")).strip())
            if fuel is not None:
                demand_vol_by_fuel[fuel] = (
                    demand_vol_by_fuel.get(fuel, 0) + abs(r["Annual_Flow"])
                )

        # ── 2b. Non-fossil supply volumes from the LF balance ─────────────
        macro_lf["Plot_Category"] = macro_lf.apply(map_macro_liquid_fuel_source, axis=1)

        macro_lf_nonfossil = macro_lf[
            macro_lf["Plot_Category"].notna()
            & macro_lf["Fuel_Commodity"].notna()
            & (macro_lf["Plot_Category"] != "Conventional Liquid Fuels")
        ].copy()

        nonfossil_by_src_fuel = (
            macro_lf_nonfossil.groupby(["Plot_Category", "Fuel_Commodity"])["Annual_Flow"]
            .apply(lambda x: x.abs().sum())
        )

        # ── 2c. Ground-truth fossil supply, read directly from the
        # refinery's own output edges (Category == "Fossil Petroleum
        # Refinery") instead of inferring fossil = demand − tracked
        # non-fossil supply. The residual is still computed below, purely
        # to validate that it agrees with the ground-truth edge value
        # rather than assuming it does.
        fossil_refinery_rows = macro_lf[
            (macro_lf["Category"] == "Fossil Petroleum Refinery")
            & macro_lf["Fuel_Commodity"].notna()
        ]
        fossil_vol_by_fuel = (
            fossil_refinery_rows
            .groupby("Fuel_Commodity")["Annual_Flow"]
            .apply(lambda x: x.abs().sum())
            .to_dict()
        )

        nonfossil_total_by_fuel = {}
        for (_, fuel_comm), vol in nonfossil_by_src_fuel.items():
            nonfossil_total_by_fuel[fuel_comm] = nonfossil_total_by_fuel.get(fuel_comm, 0) + vol

        for fuel_comm, total_demand in demand_vol_by_fuel.items():
            residual_fossil = total_demand - nonfossil_total_by_fuel.get(fuel_comm, 0)
            ground_truth_fossil = fossil_vol_by_fuel.get(fuel_comm, 0.0)
            diff = ground_truth_fossil - residual_fossil
            pct = (diff / residual_fossil * 100.0) if residual_fossil else float("nan")
            lf_fossil_checker_rows.append({
                "Scenario": scen_short,
                "Fuel": fuel_comm,
                "Residual (demand - nonfossil)": residual_fossil,
                "Ground Truth (refinery edge)": ground_truth_fossil,
                "Diff": diff,
                "Pct": pct,
                "Match": "✓" if (not pd.isna(pct) and abs(pct) < 1.0) or (residual_fossil == 0 and ground_truth_fossil == 0) else "✗",
            })

        # ── 2d. Allocate CO2 using demand as denominator ──────────────────
        lf_emissions_dict = {}

        # Non-fossil sources
        for (plot_cat, fuel_comm), vol in nonfossil_by_src_fuel.items():
            total_demand = demand_vol_by_fuel.get(fuel_comm, 0)
            actual_co2 = lf_co2_actual.get(fuel_comm, 0)
            if total_demand > 0 and actual_co2 > 0:
                lf_emissions_dict[plot_cat] = (
                    lf_emissions_dict.get(plot_cat, 0) + actual_co2 * (vol / total_demand)
                )

        # Fossil — ground truth from the refinery's own output edges
        for fuel_comm, total_demand in demand_vol_by_fuel.items():
            fossil_vol = fossil_vol_by_fuel.get(fuel_comm, 0.0)
            actual_co2 = lf_co2_actual.get(fuel_comm, 0)
            if total_demand > 0 and actual_co2 > 0 and fossil_vol > 0:
                lf_emissions_dict["Conventional Liquid Fuels"] = (
                    lf_emissions_dict.get("Conventional Liquid Fuels", 0)
                    + actual_co2 * (fossil_vol / total_demand)
                )

        for cat, val in lf_emissions_dict.items():
            macro_rows.append(
                {
                    "Scenario": scen_short,
                    "Plot_Category": cat,
                    "Value": val,
                    "Source": "Reconstructed liquid fuel end use",
                }
            )
    else:
        print(f"  Warning: no liquid fuels balance file for scenario {scen_short}, skipping liquid fuel emissions.")

    # -------------------------------------------------------------
    # 3. Reconstruct NG end-use emissions, split across ALL NG
    # production sources (fossil upstream, synthetic, bio, ethylene
    # byproduct) by each source's ground-truth share of total NG
    # production — not just a fossil-vs-synthetic split, and not a
    # "synthetic fills first" priority assumption. The shared NG
    # commodity pool is treated as well-mixed: each source's share of
    # total production is applied to the (separately, ground-truth)
    # tracked total end-use demand volume, so the four allocated
    # volumes always sum exactly back to total_ng_end_use.
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
    is_ng_end_use = edge_lower.str.contains("ng_end_use", na=False)
    total_ng_end_use = -macro_ng.loc[is_ng_end_use, "Annual_Flow"].sum()

    # Ground-truth production volumes per source. Only the positive
    # (production) side of each sector is counted — e.g. Ethylene also
    # has natgas_consumption_edge rows (steam-cracking fuel use, already
    # accounted for elsewhere via the direct CO2 balance), which must be
    # excluded here so they don't reduce the byproduct production total.
    is_fossil_upstream = macro_ng["Category"] == "NG Fossil Upstream"
    fossil_ng_production = macro_ng.loc[
        is_fossil_upstream & (macro_ng["Annual_Flow"] > 0), "Annual_Flow"
    ].sum()

    is_syn_ng = (macro_ng["Sector"] == "Synthetic fuels") & (macro_ng["Category"] == "S-NG")
    synthetic_ng_production = macro_ng.loc[
        is_syn_ng & (macro_ng["Annual_Flow"] > 0), "Annual_Flow"
    ].sum()

    is_bio_ng = macro_ng["Sector"] == "Bioenergy"
    bio_ng_production = macro_ng.loc[
        is_bio_ng & (macro_ng["Annual_Flow"] > 0), "Annual_Flow"
    ].sum()

    is_ethylene_ng = macro_ng["Sector"] == "Ethylene"
    ethylene_ng_production = macro_ng.loc[
        is_ethylene_ng & (macro_ng["Annual_Flow"] > 0), "Annual_Flow"
    ].sum()

    total_ng_production = (
        fossil_ng_production + synthetic_ng_production
        + bio_ng_production + ethylene_ng_production
    )

    if total_ng_production > 0:
        fossil_share = fossil_ng_production / total_ng_production
        synthetic_share = synthetic_ng_production / total_ng_production
        bio_share = bio_ng_production / total_ng_production
        ethylene_share = ethylene_ng_production / total_ng_production
    else:
        fossil_share = synthetic_share = bio_share = ethylene_share = 0.0

    ng_production_share_rows.append({
        "Scenario": scen_short,
        "Fossil Production (MWh)": fossil_ng_production,
        "Synthetic Production (MWh)": synthetic_ng_production,
        "Bio Production (MWh)": bio_ng_production,
        "Ethylene Production (MWh)": ethylene_ng_production,
        "Fossil Share": fossil_share,
        "Synthetic Share": synthetic_share,
        "Bio Share": bio_share,
        "Ethylene Share": ethylene_share,
    })

    fossil_ng_end_use = total_ng_end_use * fossil_share
    syn_ng_end_use = total_ng_end_use * synthetic_share
    bio_ng_end_use = total_ng_end_use * bio_share
    ethylene_ng_end_use = total_ng_end_use * ethylene_share

    fossil_ng_emission_mt = fossil_ng_end_use * ng_emission_rate * TONNE_TO_MT
    syn_ng_emission_mt = syn_ng_end_use * ng_emission_rate * TONNE_TO_MT
    bio_ng_emission_mt = bio_ng_end_use * ng_emission_rate * TONNE_TO_MT
    ethylene_ng_emission_mt = ethylene_ng_end_use * ng_emission_rate * TONNE_TO_MT

    ng_total_emission_by_scen[scen_short] = (
        fossil_ng_emission_mt + syn_ng_emission_mt
        + bio_ng_emission_mt + ethylene_ng_emission_mt
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "NG End Use",
            "Value": fossil_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Synthetic NG End Use",
            "Value": syn_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Bio NG End Use",
            "Value": bio_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    macro_rows.append(
        {
            "Scenario": scen_short,
            "Plot_Category": "Ethylene NG End Use",
            "Value": ethylene_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

    # -------------------------------------------------------------
    # 3b. NG balance validation: confirm total fossil + synthetic + bio
    # NG supply actually matches total NG demand across ALL consuming
    # sectors (End Use, Power, Hydrogen, Ethylene, DAC) — not just the
    # End-Use subset reconstructed above. The NG_Fossil_Upstream edge
    # supplies the whole zonal NG pool, so it can't be substituted
    # directly into "NG End Use" without double-counting Power/H2/
    # Ethylene NG consumption, which are already accounted for
    # elsewhere. This check only validates that the balance closes; it
    # does not change any plotted emissions value.
    #
    # Sector == "Demand" rows are excluded: those are the demand.csv
    # target values, which duplicate the model's own "NG End Use" edge
    # (Sector == "NG") — including both would double count end-use
    # demand and falsely report an imbalance.
    # -------------------------------------------------------------
    macro_ng_model = macro_ng[macro_ng["Sector"] != "Demand"]
    ng_supply_total = macro_ng_model.loc[macro_ng_model["Annual_Flow"] > 0, "Annual_Flow"].sum()
    ng_demand_total = -macro_ng_model.loc[macro_ng_model["Annual_Flow"] < 0, "Annual_Flow"].sum()
    ng_net = ng_supply_total - ng_demand_total
    ng_balance_checker_rows.append({
        "Scenario": scen_short,
        "Total NG Supply (MWh)": ng_supply_total,
        "Total NG Demand (MWh)": ng_demand_total,
        "Net (MWh)": ng_net,
        "Match": "✓" if abs(ng_net) < 1e-3 * max(ng_supply_total, 1.0) else "✗",
    })

    # -------------------------------------------------------------
    # 4. Reconstruct ethanol end-use emissions
    # -------------------------------------------------------------

    macro_ethanol_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethanol.csv",
    )

    if os.path.exists(macro_ethanol_path):
        try:
            ethanol_json_path = find_macro_asset_path(scen_short, "ethanol_end_use.json")
        except FileNotFoundError:
            scenarios_without_ethanol_end_use.append(scen_short)
        else:
            ethanol_emission_rate = read_ethanol_emission_rate(ethanol_json_path)

            macro_eth = pd.read_csv(macro_ethanol_path)
            macro_eth.columns = macro_eth.columns.str.strip()

            missing_cols = [c for c in required_cols if c not in macro_eth.columns]
            if missing_cols:
                raise ValueError(
                    f"{macro_ethanol_path} is missing required columns: {missing_cols}. "
                    f"Available columns are: {macro_eth.columns.tolist()}"
                )

            macro_eth["Annual_Flow"] = (
                pd.to_numeric(macro_eth["Annual_Flow"], errors="coerce").fillna(0.0)
            )

            macro_eth["Plot_Category"] = macro_eth.apply(map_macro_ethanol_source, axis=1)
            macro_eth = macro_eth[macro_eth["Plot_Category"].notna()].copy()

            macro_eth["End_Use_Emission_Mt"] = (
                macro_eth["Annual_Flow"].abs()
                * ethanol_emission_rate
                * TONNE_TO_MT
            )

            eth_emissions = (
                macro_eth
                .groupby("Plot_Category")["End_Use_Emission_Mt"]
                .sum()
            )

            ethanol_emission_by_scen[scen_short] = float(eth_emissions.sum())

            for category, value in eth_emissions.items():
                macro_rows.append(
                    {
                        "Scenario": scen_short,
                        "Plot_Category": category,
                        "Value": value,
                        "Source": "Reconstructed ethanol end use",
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
# Checks
# ---------------------------------------------------------------------

print("\nMACRO CO2 emission balance by scenario (Mt):")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("CO2 Emissions balance check:")
for scen in macro_combined_data.index:
    row = macro_combined_data.loc[scen]
    total_positive = row[row > 0].sum()
    total_negative = row[row < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} Mt, "
        f"Demand={total_negative:+.4f} Mt, "
        f"Net={net:+.4f} Mt  [{status}]"
    )

print("\nMACRO reconstructed emission components:")
print(
    macro_emissions_long
    .groupby(["Scenario", "Source", "Plot_Category"])["Value"]
    .sum()
    .reset_index()
)

# ---------------------------------------------------------------------
# Plot MACRO-only CO2 emission balance
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

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
ax.set_title("CO2 Emission Balance (Mt)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

_pos_ext = plot_df.clip(lower=0).sum(axis=1).max()
_neg_ext = plot_df.clip(upper=0).sum(axis=1).min()
_pad = max(abs(_pos_ext), abs(_neg_ext)) * 0.12 or 1.0
ax.set_xlim(_neg_ext - _pad, _pos_ext + _pad)
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

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

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.36)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------

_active_cols = [col for col in desired_order if plot_df[col].abs().sum() > 0]

fig_plotly = go.Figure()
for col in _active_cols:
    fig_plotly.add_trace(go.Bar(
        name=category_names.get(col, col),
        y=scenario_names,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=category_colors.get(col, '#333333'),
        hovertemplate='%{fullData.name}: %{x:.2f} Mt<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='CO2 Emission Balance (Mt)',
    xaxis_title='Mt',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

# ---------------------------------------------------------------------------
# Combustion emission checker: expected (demand × rate × 8760) vs plotted
# ---------------------------------------------------------------------------

def compute_expected_combustion(demand_path):
    """
    Expected annual combustion emissions (Mt CO2) using the first time-step
    demand (MW) × 8760 h × carbon_end_use_dict rate (tCO2/MWh) × 1e-6.

    Liquid fuels are global (one column); NG is summed across all zones.
    """
    demand = pd.read_csv(demand_path)
    demand.columns = demand.columns.str.strip()
    row = demand.sort_values("Time_Index").iloc[0]

    col_prefixes = {
        "gasoline":   "gasoline_mw_",
        "jetfuel":    "jetfuel_mw_",
        "diesel":     "diesel_mw_",
        "ethanol":    "ethanol_mw",
        "naturalgas": "naturalgas_mw_",
    }

    result = {}
    for commodity, prefix in col_prefixes.items():
        cols = [c for c in row.index if c.lower().startswith(prefix)]
        demand_mw = 0.0
        if cols:
            demand_mw = float(
                pd.to_numeric(
                    pd.Series([row[c] for c in cols]),
                    errors="coerce",
                ).fillna(0.0).sum()
            )
        rate = carbon_end_use_dict.get(commodity, 0.0)
        result[commodity] = {
            "demand_mw": demand_mw,
            "expected_mt": demand_mw * 8760.0 * rate * TONNE_TO_MT,
        }
    return result


checker_rows = []
for scen_short in macro_scenario_paths:
    dpath = demand_path_by_scen.get(scen_short)
    if not dpath or not os.path.exists(dpath):
        print(f"  Warning: demand.csv not found for {scen_short}, skipping checker.")
        continue

    expected = compute_expected_combustion(dpath)
    lf_actual = lf_co2_actual_by_scen.get(scen_short, {})

    plotted = {
        "gasoline":   lf_actual.get("Gasoline", 0.0),
        "jetfuel":    lf_actual.get("JetFuel", 0.0),
        "diesel":     lf_actual.get("Diesel", 0.0),
        "naturalgas": ng_total_emission_by_scen.get(scen_short, 0.0),
        "ethanol":    ethanol_emission_by_scen.get(scen_short, 0.0),
    }

    for commodity in carbon_end_use_dict:
        exp_mt = expected.get(commodity, {}).get("expected_mt", 0.0)
        dem_mw = expected.get(commodity, {}).get("demand_mw", 0.0)
        plt_mt = plotted.get(commodity, 0.0)
        diff = plt_mt - exp_mt
        pct = (diff / exp_mt * 100.0) if exp_mt != 0.0 else float("nan")
        checker_rows.append({
            "Scenario": scen_short,
            "Commodity": commodity,
            "Demand MW": dem_mw,
            "Expected Mt": exp_mt,
            "Plotted Mt": plt_mt,
            "Diff Mt": diff,
            "Pct": pct,
            "Match": "✓" if (not pd.isna(pct) and abs(pct) < 1.0) else "✗",
        })

checker_df = pd.DataFrame(checker_rows)

print("\n" + "=" * 90)
print("COMBUSTION EMISSION CHECKER  [expected = demand_MW × 8760 h × rate (tCO2/MWh) × 1e-6]")
print("=" * 90)
if not checker_df.empty:
    _disp = checker_df.copy()
    _disp["Demand MW"]   = _disp["Demand MW"].map(lambda x: f"{x:,.0f}")
    _disp["Expected Mt"] = _disp["Expected Mt"].map(lambda x: f"{x:.4f}")
    _disp["Plotted Mt"]  = _disp["Plotted Mt"].map(lambda x: f"{x:.4f}")
    _disp["Diff Mt"]     = _disp["Diff Mt"].map(lambda x: f"{x:+.4f}")
    _disp["Pct"]         = _disp["Pct"].map(lambda x: f"{x:+.1f}%" if not pd.isna(x) else "N/A")
    print(
        _disp.rename(columns={
            "Demand MW": "Demand (MW)", "Expected Mt": "Expected (Mt)",
            "Plotted Mt": "Plotted (Mt)", "Diff Mt": "Diff (Mt)",
            "Pct": "Δ%", "Match": "✓/✗",
        }).to_string(index=False)
    )
else:
    print("  No checker data available.")

lf_fossil_checker_df = pd.DataFrame(lf_fossil_checker_rows)

print("\n" + "=" * 90)
print("LIQUID FUEL FOSSIL VOLUME CHECKER  [residual (demand - nonfossil) vs ground truth (refinery edge)]")
print("=" * 90)
if not lf_fossil_checker_df.empty:
    _disp = lf_fossil_checker_df.copy()
    _disp["Residual (demand - nonfossil)"] = _disp["Residual (demand - nonfossil)"].map(lambda x: f"{x:,.1f}")
    _disp["Ground Truth (refinery edge)"]  = _disp["Ground Truth (refinery edge)"].map(lambda x: f"{x:,.1f}")
    _disp["Diff"] = _disp["Diff"].map(lambda x: f"{x:+,.1f}")
    _disp["Pct"]  = _disp["Pct"].map(lambda x: f"{x:+.2f}%" if not pd.isna(x) else "N/A")
    print(_disp.rename(columns={"Pct": "Δ%", "Match": "✓/✗"}).to_string(index=False))
else:
    print("  No liquid fuel fossil checker data available.")

ng_balance_checker_df = pd.DataFrame(ng_balance_checker_rows)

print("\n" + "=" * 90)
print("NG COMMODITY BALANCE CHECKER  [total supply (fossil+synthetic+bio) vs total demand (end use+power+H2+ethylene+DAC)]")
print("=" * 90)
if not ng_balance_checker_df.empty:
    _disp = ng_balance_checker_df.copy()
    _disp["Total NG Supply (MWh)"] = _disp["Total NG Supply (MWh)"].map(lambda x: f"{x:,.1f}")
    _disp["Total NG Demand (MWh)"] = _disp["Total NG Demand (MWh)"].map(lambda x: f"{x:,.1f}")
    _disp["Net (MWh)"]             = _disp["Net (MWh)"].map(lambda x: f"{x:+,.1f}")
    print(_disp.rename(columns={"Match": "✓/✗"}).to_string(index=False))
else:
    print("  No NG balance checker data available.")

ng_production_share_df = pd.DataFrame(ng_production_share_rows)

print("\n" + "=" * 90)
print("NG END USE PRODUCTION-SHARE ALLOCATION  [share of total NG production used to split NG End Use emissions]")
print("=" * 90)
if not ng_production_share_df.empty:
    _disp = ng_production_share_df.copy()
    for col in ["Fossil Production (MWh)", "Synthetic Production (MWh)",
                "Bio Production (MWh)", "Ethylene Production (MWh)"]:
        _disp[col] = _disp[col].map(lambda x: f"{x:,.1f}")
    for col in ["Fossil Share", "Synthetic Share", "Bio Share", "Ethylene Share"]:
        _disp[col] = _disp[col].map(lambda x: f"{x:.2%}")
    print(_disp.to_string(index=False))
else:
    print("  No NG production-share data available.")

# ---------------------------------------------------------------------------
# Estimated emissions total and by type
# ---------------------------------------------------------------------------

_COMBUSTION = [
    "Conventional Liquid Fuels", "Conventional NG", "NG End Use",
    "Synthetic Fuels Combustion", "Synthetic NG End Use",
    "Bio NG End Use", "Ethylene NG End Use",
    "Biofuels Combustion", "Ethanol Combustion", "Ethanol LF Combustion",
]
_PROCESS = [
    "Synthetic Fuels and processes", "Synthetic NG and processes",
    "Biofuels and processes", "Ethylene and processes", "Ethanol and processes",
]
_REMOVAL = ["Biomass Capture", "Ethanol Biomass Capture", "DAC Capture"]

summary_rows = []
for scen in macro_combined_data.index:
    r = macro_combined_data.loc[scen]
    combustion_mt = sum(max(r.get(c, 0.0), 0.0) for c in _COMBUSTION)
    process_mt    = sum(max(r.get(c, 0.0), 0.0) for c in _PROCESS)
    removal_mt    = sum(r.get(c, 0.0) for c in _REMOVAL)
    gross_mt      = float(r[r > 0].sum())
    net_mt        = float(r.sum())
    summary_rows.append({
        "Scenario":        scen,
        "Gross (Mt)":      gross_mt,
        "Combustion (Mt)": combustion_mt,
        "Process (Mt)":    process_mt,
        "Removal (Mt)":    removal_mt,
        "Net (Mt)":        net_mt,
    })

summary_df = pd.DataFrame(summary_rows)

print("\n" + "=" * 90)
print("ESTIMATED CO2 EMISSIONS BY TYPE (Mt CO2)")
print("=" * 90)
if not summary_df.empty:
    _sdisp = summary_df.copy()
    for col in [c for c in _sdisp.columns if c != "Scenario"]:
        _sdisp[col] = _sdisp[col].map(lambda x: f"{x:.3f}")
    print(_sdisp.to_string(index=False))

# ---------------------------------------------------------------------------
# Plotly tables for checker and summary
# ---------------------------------------------------------------------------

def _make_checker_table(df):
    if df.empty:
        return go.Figure()
    col_labels = ["Scenario", "Commodity", "Demand (MW)", "Expected (Mt)",
                  "Plotted (Mt)", "Diff (Mt)", "Δ%", "✓/✗"]
    col_keys   = ["Scenario", "Commodity", "Demand MW", "Expected Mt",
                  "Plotted Mt", "Diff Mt", "Pct", "Match"]
    cells_data = []
    for key in col_keys:
        vals = df[key].tolist()
        if key == "Demand MW":
            vals = [f"{v:,.0f}" for v in vals]
        elif key in ("Expected Mt", "Plotted Mt"):
            vals = [f"{v:.4f}" for v in vals]
        elif key == "Diff Mt":
            vals = [f"{v:+.4f}" for v in vals]
        elif key == "Pct":
            vals = [f"{v:+.1f}%" if not pd.isna(v) else "N/A" for v in vals]
        cells_data.append(vals)
    status_colors = ["lightgreen" if m == "✓" else "lightcoral" for m in df["Match"].tolist()]
    n_data_cols = len(col_labels) - 1
    fill_colors = [["white"] * len(df)] * n_data_cols + [status_colors]
    return go.Figure(
        data=[go.Table(
            header=dict(values=col_labels, fill_color="lightsteelblue", align="left",
                        font=dict(size=12, color="black")),
            cells=dict(values=cells_data, fill_color=fill_colors, align="left",
                       font=dict(size=11)),
        )],
        layout=go.Layout(
            title="Combustion Emission Checker: Expected vs Plotted (Mt CO2)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=max(200, 35 * (len(df) + 3)),
        ),
    )


def _make_summary_table(df):
    if df.empty:
        return go.Figure()
    col_labels = list(df.columns)
    cells_data = []
    for col in col_labels:
        vals = df[col].tolist()
        if col != "Scenario":
            vals = [f"{v:.3f}" for v in vals]
        cells_data.append(vals)
    return go.Figure(
        data=[go.Table(
            header=dict(values=col_labels, fill_color="lightsteelblue", align="left",
                        font=dict(size=12, color="black")),
            cells=dict(values=cells_data, align="left", font=dict(size=11)),
        )],
        layout=go.Layout(
            title="Estimated CO2 Emissions by Type (Mt CO2)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=max(150, 35 * (len(df) + 3)),
        ),
    )


def _make_lf_fossil_checker_table(df):
    if df.empty:
        return go.Figure()
    col_labels = ["Scenario", "Fuel", "Residual (demand - nonfossil)",
                  "Ground Truth (refinery edge)", "Diff", "Δ%", "✓/✗"]
    col_keys   = ["Scenario", "Fuel", "Residual (demand - nonfossil)",
                  "Ground Truth (refinery edge)", "Diff", "Pct", "Match"]
    cells_data = []
    for key in col_keys:
        vals = df[key].tolist()
        if key in ("Residual (demand - nonfossil)", "Ground Truth (refinery edge)"):
            vals = [f"{v:,.1f}" for v in vals]
        elif key == "Diff":
            vals = [f"{v:+,.1f}" for v in vals]
        elif key == "Pct":
            vals = [f"{v:+.2f}%" if not pd.isna(v) else "N/A" for v in vals]
        cells_data.append(vals)
    status_colors = ["lightgreen" if m == "✓" else "lightcoral" for m in df["Match"].tolist()]
    n_data_cols = len(col_labels) - 1
    fill_colors = [["white"] * len(df)] * n_data_cols + [status_colors]
    return go.Figure(
        data=[go.Table(
            header=dict(values=col_labels, fill_color="lightsteelblue", align="left",
                        font=dict(size=12, color="black")),
            cells=dict(values=cells_data, fill_color=fill_colors, align="left",
                       font=dict(size=11)),
        )],
        layout=go.Layout(
            title="Liquid Fuel Fossil Volume Checker: Residual vs Ground Truth (MWh)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=max(200, 35 * (len(df) + 3)),
        ),
    )


def _make_ng_balance_checker_table(df):
    if df.empty:
        return go.Figure()
    col_labels = ["Scenario", "Total NG Supply (MWh)", "Total NG Demand (MWh)", "Net (MWh)", "✓/✗"]
    col_keys   = ["Scenario", "Total NG Supply (MWh)", "Total NG Demand (MWh)", "Net (MWh)", "Match"]
    cells_data = []
    for key in col_keys:
        vals = df[key].tolist()
        if key in ("Total NG Supply (MWh)", "Total NG Demand (MWh)"):
            vals = [f"{v:,.1f}" for v in vals]
        elif key == "Net (MWh)":
            vals = [f"{v:+,.1f}" for v in vals]
        cells_data.append(vals)
    status_colors = ["lightgreen" if m == "✓" else "lightcoral" for m in df["Match"].tolist()]
    n_data_cols = len(col_labels) - 1
    fill_colors = [["white"] * len(df)] * n_data_cols + [status_colors]
    return go.Figure(
        data=[go.Table(
            header=dict(values=col_labels, fill_color="lightsteelblue", align="left",
                        font=dict(size=12, color="black")),
            cells=dict(values=cells_data, fill_color=fill_colors, align="left",
                       font=dict(size=11)),
        )],
        layout=go.Layout(
            title="NG Commodity Balance Checker: Total Supply vs Total Demand (MWh)",
            margin=dict(l=10, r=10, t=40, b=10),
            height=max(200, 35 * (len(df) + 3)),
        ),
    )


def _make_ng_production_share_table(df):
    if df.empty:
        return go.Figure()
    col_labels = ["Scenario", "Fossil Production (MWh)", "Synthetic Production (MWh)",
                  "Bio Production (MWh)", "Ethylene Production (MWh)",
                  "Fossil Share", "Synthetic Share", "Bio Share", "Ethylene Share"]
    col_keys = col_labels
    cells_data = []
    for key in col_keys:
        vals = df[key].tolist()
        if "Production" in key:
            vals = [f"{v:,.1f}" for v in vals]
        elif "Share" in key:
            vals = [f"{v:.2%}" for v in vals]
        cells_data.append(vals)
    return go.Figure(
        data=[go.Table(
            header=dict(values=col_labels, fill_color="lightsteelblue", align="left",
                        font=dict(size=12, color="black")),
            cells=dict(values=cells_data, align="left", font=dict(size=11)),
        )],
        layout=go.Layout(
            title="NG End Use Production-Share Allocation",
            margin=dict(l=10, r=10, t=40, b=10),
            height=max(200, 35 * (len(df) + 3)),
        ),
    )


checker_plotly = _make_checker_table(checker_df)
summary_plotly = _make_summary_table(summary_df)
lf_fossil_checker_plotly = _make_lf_fossil_checker_table(lf_fossil_checker_df)
ng_balance_checker_plotly = _make_ng_balance_checker_table(ng_balance_checker_df)
ng_production_share_plotly = _make_ng_production_share_table(ng_production_share_df)

# Expose extra figures so Run_All_Macro_Plots.py can include them in the combined HTML.
extra_plotly_figs   = [
    checker_plotly, summary_plotly, lf_fossil_checker_plotly,
    ng_balance_checker_plotly, ng_production_share_plotly,
]
extra_plotly_titles = [
    "CO2 Emission Checker", "CO2 Emissions by Type",
    "Liquid Fuel Fossil Volume Checker", "NG Commodity Balance Checker",
    "NG End Use Production-Share Allocation",
]

# ---------------------------------------------------------------------------
# Write combined HTML: bar chart + checker table + summary table
# ---------------------------------------------------------------------------

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_emission_macro_interactive.html')
with open(html_path, 'w') as _hf:
    _hf.write('<html><head><title>CO2 Emission Balance</title></head><body>\n')
    _hf.write('<h2 style="font-family:Arial">CO2 Emission Balance (Mt)</h2>\n')
    _hf.write(fig_plotly.to_html(full_html=False, include_plotlyjs='cdn'))
    _hf.write('<h2 style="font-family:Arial">Combustion Emission Checker</h2>\n')
    _hf.write(
        '<p style="font-family:Arial;font-size:12px">'
        'Expected = demand_MW &times; 8760 h &times; rate (tCO2/MWh) &times; 1e&#8209;6'
        ' &nbsp;|&nbsp; Threshold: &lt;1% difference = ✓'
        '</p>\n'
    )
    _hf.write(checker_plotly.to_html(full_html=False, include_plotlyjs=False))
    _hf.write('<h2 style="font-family:Arial">Estimated CO2 Emissions by Type</h2>\n')
    _hf.write(summary_plotly.to_html(full_html=False, include_plotlyjs=False))
    _hf.write('<h2 style="font-family:Arial">Liquid Fuel Fossil Volume Checker</h2>\n')
    _hf.write(
        '<p style="font-family:Arial;font-size:12px">'
        'Ground truth fossil volume is read directly from the refinery\'s own output edges '
        '(Category == "Fossil Petroleum Refinery") instead of being inferred as demand &minus; '
        'tracked non-fossil supply. &nbsp;|&nbsp; Threshold: &lt;1% difference = ✓'
        '</p>\n'
    )
    _hf.write(lf_fossil_checker_plotly.to_html(full_html=False, include_plotlyjs=False))
    _hf.write('<h2 style="font-family:Arial">NG Commodity Balance Checker</h2>\n')
    _hf.write(
        '<p style="font-family:Arial;font-size:12px">'
        'Validates that total NG supply (fossil upstream + synthetic + bio) matches total NG '
        'demand across ALL consuming sectors (End Use, Power, Hydrogen, Ethylene, DAC), not just '
        'the End-Use subset reconstructed above. Does not change any plotted emissions value.'
        '</p>\n'
    )
    _hf.write(ng_balance_checker_plotly.to_html(full_html=False, include_plotlyjs=False))
    _hf.write('<h2 style="font-family:Arial">NG End Use Production-Share Allocation</h2>\n')
    _hf.write(
        '<p style="font-family:Arial;font-size:12px">'
        'NG End Use emissions are split across fossil/synthetic/bio/ethylene-byproduct NG '
        'in proportion to each source\'s ground-truth share of total NG production (fossil '
        'upstream edge, synthetic S-NG plant output, bioenergy NG production, and Ethylene '
        'sector NG byproduct production). The four allocated volumes always sum back to the '
        'tracked total NG End Use demand.'
        '</p>\n'
    )
    _hf.write(ng_production_share_plotly.to_html(full_html=False, include_plotlyjs=False))
    _hf.write('</body></html>')

webbrowser.open(f'file://{html_path}')

if scenarios_without_ethanol_end_use:
    print("\nException: the following scenarios do not have ethanol end use (ethanol_end_use.json not found):")
    for s in scenarios_without_ethanol_end_use:
        print(f"  Scenario {s}")