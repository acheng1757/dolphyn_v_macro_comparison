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
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_input_paths, macro_scenario_paths

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
    "Biofuels and processes": "Biofuels Process",
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

required_cols = ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]

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
        # Fossil supply is incomplete in the balance file for scenarios where
        # it acts as residual supplier, so we derive fossil = demand − non-fossil.
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

        # ── 2c. Allocate CO2 using demand as denominator ──────────────────
        lf_emissions_dict = {}

        # Non-fossil sources
        for (plot_cat, fuel_comm), vol in nonfossil_by_src_fuel.items():
            total_demand = demand_vol_by_fuel.get(fuel_comm, 0)
            actual_co2 = lf_co2_actual.get(fuel_comm, 0)
            if total_demand > 0 and actual_co2 > 0:
                lf_emissions_dict[plot_cat] = (
                    lf_emissions_dict.get(plot_cat, 0) + actual_co2 * (vol / total_demand)
                )

        # Fossil = demand − sum of all tracked non-fossil supply
        nonfossil_total_by_fuel = {}
        for (_, fuel_comm), vol in nonfossil_by_src_fuel.items():
            nonfossil_total_by_fuel[fuel_comm] = nonfossil_total_by_fuel.get(fuel_comm, 0) + vol

        for fuel_comm, total_demand in demand_vol_by_fuel.items():
            fossil_vol = total_demand - nonfossil_total_by_fuel.get(fuel_comm, 0)
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
    is_ng_end_use = edge_lower.str.contains("ng_end_use", na=False)
    total_ng_end_use = -macro_ng.loc[is_ng_end_use, "Annual_Flow"].sum()

    # Synthetic NG production/supply. These rows are usually positive.
    is_syn_ng_supply = edge_lower.str.contains("syn_ng", na=False)
    syn_ng_supply = macro_ng.loc[is_syn_ng_supply, "Annual_Flow"].sum()

    # Cap synthetic NG assigned to end-use emissions by total NG end-use demand.
    syn_ng_end_use = min(max(syn_ng_supply, 0.0), max(total_ng_end_use, 0.0))
    fossil_ng_end_use = max(total_ng_end_use - syn_ng_end_use, 0.0)

    syn_ng_emission_mt = syn_ng_end_use * ng_emission_rate * TONNE_TO_MT
    fossil_ng_emission_mt = fossil_ng_end_use * ng_emission_rate * TONNE_TO_MT

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
            "Plot_Category": "NG End Use",
            "Value": fossil_ng_emission_mt,
            "Source": "Reconstructed NG end use",
        }
    )

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

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_emission_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')

if scenarios_without_ethanol_end_use:
    print("\nException: the following scenarios do not have ethanol end use (ethanol_end_use.json not found):")
    for s in scenarios_without_ethanol_end_use:
        print(f"  Scenario {s}")