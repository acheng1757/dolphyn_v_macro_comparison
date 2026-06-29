#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths, macro_input_paths

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

MWH_TO_EJ = 3.6e-9  # 1 MWh = 3.6e9 J; 1 EJ = 1e18 J

# ---------------------------------------------------------------------
# Desired order, colors, and labels (same styling as ETHANOL_Macro.py,
# minus the two non-zonal global demand rows, which have no per-zone
# breakdown in this dataset)
# ---------------------------------------------------------------------

desired_order = [
    "DryMill_Existing_Non_CCS",
    "DryMill_CCS_Fermentation_RETROFIT",
    "DryMill_CCS_Fermentation_Exhaust_RETROFIT",
    "DryMill_CCS_Fermentation",
    "DryMill_CCS_Fermentation_Exhaust",
    "Bio_Ethanol_CCS_20",
    "Bio_Ethanol_CCS_86",
    "Bio_Ethanol_Non_CCS",
    "Ethylene",
    "Ethanol to Gasoline",
    "Ethanol to Diesel",
    "Ethanol to JetFuel",
    "Ethanol to Gasoline Diesel",
]

category_colors = {
    "Bio_Ethanol_Non_CCS":      "#f0cc6a",
    "Bio_Ethanol_CCS_20":       "#d4a017",
    "Bio_Ethanol_CCS_86":       "#8b6500",
    "DryMill_Existing_Non_CCS": "#f4a86a",
    "DryMill_CCS_Fermentation_RETROFIT":  "#e8630a",   # same as DryMill_CCS_Fermentation
    "DryMill_CCS_Fermentation_Exhaust_RETROFIT":  "#7a2e0e",   # same as DryMill_CCS_Fermentation_Exhaust
    "DryMill_CCS_Fermentation":           "#e8630a",
    "DryMill_CCS_Fermentation_Exhaust":           "#7a2e0e",
    "Ethylene":                 "#e8630a",
    "Ethanol to Gasoline":       "royalblue",
    "Ethanol to Diesel":         "forestgreen",
    "Ethanol to JetFuel":        "chocolate",
    "Ethanol to Gasoline Diesel": "limegreen",
}

# Pattern encodes build type: "" = new build, "//" = retrofit, ".." = existing
category_hatch = {
    "Bio_Ethanol_Non_CCS":      "",
    "Bio_Ethanol_CCS_20":       "",
    "Bio_Ethanol_CCS_86":       "",
    "DryMill_Existing_Non_CCS": "..",
    "DryMill_CCS_Fermentation_RETROFIT":         "//",
    "DryMill_CCS_Fermentation_Exhaust_RETROFIT": "//",
    "DryMill_CCS_Fermentation":                  "",
    "DryMill_CCS_Fermentation_Exhaust":          "",
    "Ethylene":                  "",
    "Ethanol to Gasoline":       "",
    "Ethanol to Diesel":         "",
    "Ethanol to JetFuel":        "",
    "Ethanol to Gasoline Diesel": "",
}

label_map = {
    "DryMill_Existing_Non_CCS":  "DryMill_Existing_Non_CCS",
    "DryMill_CCS_Fermentation_RETROFIT":   "DryMill_CCS_Fermentation_RETROFIT",
    "DryMill_CCS_Fermentation_Exhaust_RETROFIT":   "DryMill_CCS_Fermentation_Exhaust_RETROFIT",
    "DryMill_CCS_Fermentation":            "DryMill_CCS_Fermentation",
    "DryMill_CCS_Fermentation_Exhaust":            "DryMill_CCS_Fermentation_Exhaust",
    "Bio_Ethanol_CCS_20":        "Bio_Ethanol_CCS_20",
    "Bio_Ethanol_CCS_86":        "Bio_Ethanol_CCS_86",
    "Bio_Ethanol_Non_CCS":       "Bio_Ethanol_Non_CCS",
    "Ethylene":                  "Ethylene",
    "Ethanol to Gasoline":       "Eth. Upgrading (Gasoline)",
    "Ethanol to Diesel":         "Eth. Upgrading (Diesel)",
    "Ethanol to JetFuel":        "Eth. Upgrading (JetFuel)",
    "Ethanol to Gasoline Diesel": "Eth. Upgrading (Gasoline+Diesel)",
}

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
# Canonical zone order, matching the column order in demand.csv
# (e.g. Electricity_MW_CA, Electricity_MW_NW, ...).
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name.

    Production/consumption edges are named like:
        SE_Bio_Ethanol_CCS_20_Agri_ethanol_production_edge
        MIDAT_DryMill_Existing_Non_CCS_ethanol_production_edge
        TX_B-H2in_ethanol_consumption_edge
        NE_Ethanol_to_Diesel_ethanol_consumption_edge

    System-wide edges (e.g. the global Ethanol_MW_Global demand row)
    have no zone and return None.
    """
    tokens = str(edge_name).split("_")
    candidates = tokens[:1]
    if tokens[:1] == ["Existing"] and len(tokens) > 1:
        candidates.append(tokens[1])

    for candidate in candidates:
        if candidate in zone_list:
            return candidate

    return None


# ---------------------------------------------------------------------
# MACRO ethanol balance mapping (same as ETHANOL_Macro.py)
# ---------------------------------------------------------------------

def map_macro_ethanol_category(row):
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()

    # Ethanol production technologies
    if sector == "Ethanol":
        return category

    # Dehydration plants in the Ethylene sector consuming ethanol
    if sector == "Ethylene":
        return "Ethylene"

    # Ethanol demand rows from demand.csv (single global node, no zone)
    if sector == "Demand":
        return "Ethanol Demand"

    return None


# ---------------------------------------------------------------------
# Ethanol-to-X upgrading consumption, by zone
# ---------------------------------------------------------------------
# Ethanol_to_X assets are tagged as "Ethanol Upgrading" in Step 1, so they
# are absent from the Ethanol balance file's Category column. We pull
# their ethanol_consumption_edge annual flows (already negative) directly
# from the all_nonzero file, one category per process, grouped by zone.

_ETHANOL_UPGRADING_ASSETS = [
    ("Ethanol to Gasoline",       "_Ethanol_to_Gasoline_",       "_Ethanol_to_Gasoline_Diesel_"),
    ("Ethanol to Gasoline Diesel", "_Ethanol_to_Gasoline_Diesel_", None),
    ("Ethanol to Diesel JetFuel", "_Ethanol_to_Diesel_JetFuel_", None),
    ("Ethanol to Diesel",         "_Ethanol_to_Diesel_",         "_Ethanol_to_Diesel_JetFuel_"),
    ("Ethanol to JetFuel",        "_Ethanol_to_JetFuel_",        None),
]


def _load_ethanol_upgrading_consumption_by_zone(results_dir):
    """Return {plot_category: {zone: annual_ethanol_consumption_MWh}} for each Ethanol_to_X process."""
    path = os.path.join(
        results_dir,
        "annual_flow_results",
        "all_nonzero_annual_flows_with_categories.csv",
    )
    result = {cat: {} for cat, _, _ in _ETHANOL_UPGRADING_ASSETS}
    if not os.path.exists(path):
        return result
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    if "Edge" not in df.columns or "Annual_Flow" not in df.columns:
        return result
    flows = pd.to_numeric(df["Annual_Flow"], errors="coerce").fillna(0.0)
    zones = df["Edge"].apply(extract_zone)
    for cat, include, exclude in _ETHANOL_UPGRADING_ASSETS:
        mask = (
            df["Edge"].str.contains(include, na=False) &
            df["Edge"].str.endswith("_ethanol_consumption_edge")
        )
        if exclude is not None:
            mask &= ~df["Edge"].str.contains(exclude, na=False)
        result[cat] = flows[mask].groupby(zones[mask]).sum().to_dict()
    return result


# ---------------------------------------------------------------------
# Read MACRO ethanol balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
unzoned_by_scenario = {}

for scen_short, scen_path in macro_scenario_paths.items():
    macro_eth_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethanol.csv",
    )

    if not os.path.exists(macro_eth_path):
        print(f"Warning: MACRO ethanol balance file not found: {macro_eth_path}")
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

    macro_eth["Annual_Flow"] = (
        pd.to_numeric(macro_eth["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * MWH_TO_EJ
    )

    macro_eth["Plot_Category"] = macro_eth.apply(map_macro_ethanol_category, axis=1)
    macro_eth["Zone"] = macro_eth["Edge"].apply(extract_zone)

    # Keep only rows that belong to a specific zone and a plotted category.
    # This naturally drops the global, non-zonal Ethanol Demand row.
    macro_eth_zoned = macro_eth[
        macro_eth["Zone"].notna() &
        macro_eth["Plot_Category"].isin(desired_order)
    ].copy()

    # Rows in a plotted category that didn't get a zone assigned would be
    # silently dropped from the by-zone tables above; track their total
    # so the coverage check below can flag any gap.
    unzoned = macro_eth[
        macro_eth["Zone"].isna() &
        macro_eth["Plot_Category"].isin(desired_order)
    ]
    unzoned_by_scenario[scen_short] = unzoned["Annual_Flow"].sum()

    zone_table = (
        macro_eth_zoned
        .groupby(["Zone", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .reindex(zone_list)
        .fillna(0.0)
    )

    for col in desired_order:
        if col not in zone_table.columns:
            zone_table[col] = 0.0

    # Merge in the Ethanol-to-X upgrading consumption, by zone (EJ).
    results_dir = os.path.join(macro_base_dir, scen_path)
    upgrading_by_zone = _load_ethanol_upgrading_consumption_by_zone(results_dir)
    for cat in ["Ethanol to Gasoline", "Ethanol to Diesel", "Ethanol to JetFuel", "Ethanol to Gasoline Diesel"]:
        zone_vals = upgrading_by_zone.get(cat, {})
        for zone, raw_flow in zone_vals.items():
            if zone in zone_table.index:
                zone_table.loc[zone, cat] = raw_flow * MWH_TO_EJ

    zone_table = zone_table[desired_order]
    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nEthanol production/consumption by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Per-zone existing DryMill capacity (for reference lines)
# ---------------------------------------------------------------------

existing_drymill_cap_by_zone = {}

_drymill_json_path = os.path.join(
    macro_base_dir,
    macro_input_paths[scenario_names[0]],
    "assets",
    "existing_drymill.json",
)

if os.path.exists(_drymill_json_path):
    with open(_drymill_json_path) as _f:
        _drymill = json.load(_f)

    _mwh_ethanol_p_t_biomass = (
        _drymill["drymill"][0]["instance_data"][0]["transforms"]["ethanol_production"]
    )

    _biomass_cap_t_per_hr_by_zone = {}
    for asset in _drymill["drymill"]:
        for inst in asset["instance_data"]:
            zone = str(inst["id"]).split("_")[0]
            if zone not in zone_list:
                continue
            cap = inst["edges"]["biomass_consumption_edge"]["existing_capacity"]
            _biomass_cap_t_per_hr_by_zone[zone] = _biomass_cap_t_per_hr_by_zone.get(zone, 0.0) + cap

    # t-biomass/hr × MWh-ethanol/t-biomass × 8760 hr/yr × EJ/MWh → EJ/yr
    existing_drymill_cap_by_zone = {
        zone: cap * _mwh_ethanol_p_t_biomass * 8760 * MWH_TO_EJ
        for zone, cap in _biomass_cap_t_per_hr_by_zone.items()
    }
else:
    print(f"Warning: existing DryMill capacity file not found: {_drymill_json_path}")


# ---------------------------------------------------------------------
# Determine plotted scenarios and active categories
# ---------------------------------------------------------------------

plotted_scenarios = [s for s in scenario_names if s in zone_tables_by_scenario]

# Union of categories that are actually non-trivial in at least one scenario,
# preserving desired_order, so the legend/colors stay consistent across panels.
active_cols = [
    col for col in desired_order
    if any(
        zone_tables_by_scenario[s][col].abs().sum() > 1e-6
        for s in plotted_scenarios
    )
]

# ---------------------------------------------------------------------------
# Interactive Plotly version — one subplot per scenario, hover for details
# ---------------------------------------------------------------------------

_plotly_hatch_map = {"//": "/", "..": "."}

fig_plotly = make_subplots(
    rows=len(plotted_scenarios),
    cols=1,
    shared_xaxes=True,
    subplot_titles=[f"Scenario {s}" for s in plotted_scenarios],
    vertical_spacing=0.4 / len(plotted_scenarios) if len(plotted_scenarios) > 1 else 0.1,
)

legend_shown = set()
capacity_legend_shown = False

for row_idx, scen in enumerate(plotted_scenarios, start=1):
    plot_df = zone_tables_by_scenario[scen][active_cols]

    for col in active_cols:
        display_name = label_map.get(col, col)
        color = category_colors.get(col, "#333333")
        pattern_shape = _plotly_hatch_map.get(category_hatch.get(col, ""), "")

        fig_plotly.add_trace(
            go.Bar(
                name=display_name,
                y=zone_list,
                x=plot_df[col].tolist(),
                orientation="h",
                marker_color=color,
                marker_pattern_shape=pattern_shape,
                marker_pattern_fgcolor="white",
                marker_pattern_fillmode="overlay",
                hovertemplate="%{fullData.name}: %{x:.4f} EJ<extra></extra>",
                legendgroup=col,
                showlegend=col not in legend_shown,
            ),
            row=row_idx,
            col=1,
        )
        legend_shown.add(col)

    fig_plotly.update_yaxes(autorange="reversed", row=row_idx, col=1)
    fig_plotly.add_shape(
        dict(
            type="line", x0=0, x1=0, y0=-0.5, y1=len(zone_list) - 0.5,
            line=dict(color="black", width=1, dash="dash"),
        ),
        row=row_idx, col=1,
    )

    for i, zone in enumerate(zone_list):
        cap = existing_drymill_cap_by_zone.get(zone, 0.0)
        if cap <= 1e-9:
            continue
        #fig_plotly.add_shape(
        #    dict(
        #        type="line", x0=cap, x1=cap, y0=i - 0.4, y1=i + 0.4,
        #        line=dict(color="red", width=1.5, dash="dash"),
        #    ),
        #    row=row_idx, col=1,
        #)
        fig_plotly.add_shape(
            dict(
                type="line", x0=0.9 * cap, x1=0.9 * cap, y0=i - 0.4, y1=i + 0.4,
                line=dict(color="red", width=1, dash="dot"),
            ),
            row=row_idx, col=1,
        )

    if not capacity_legend_shown and any(existing_drymill_cap_by_zone.values()):
        #fig_plotly.add_trace(
        #    go.Scatter(
        #        x=[None], y=[None], mode="lines",
        #        line=dict(color="red", width=1.5, dash="dash"),
        #        name="Total Existing Capacity",
        #    ),
        #    row=row_idx, col=1,
        #)
        fig_plotly.add_trace(
            go.Scatter(
                x=[None], y=[None], mode="lines",
                line=dict(color="red", width=1, dash="dot"),
                name="90% Existing Capacity",
            ),
            row=row_idx, col=1,
        )
        capacity_legend_shown = True

fig_plotly.update_layout(
    barmode="relative",
    title="Ethanol Production & Consumption by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ethanol_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Coverage check: per scenario, total production, total consumption, and
# net, plus a flag for any plotted-category rows that didn't get a zone
# assigned (which would otherwise be silently missing from the plots above).
# ---------------------------------------------------------------------------
print("\nEthanol by-zone coverage check:")
for scen in plotted_scenarios:
    table = zone_tables_by_scenario[scen]
    total_production = table[table > 0].sum().sum()
    total_consumption = table[table < 0].sum().sum()
    net = total_production + total_consumption
    unzoned_total = unzoned_by_scenario.get(scen, 0.0)
    status = "OK" if abs(unzoned_total) < 1e-6 else "WARNING: unzoned rows found"
    print(
        f"  Scenario {scen}: Production={total_production:+.4f} EJ, "
        f"Consumption={total_consumption:+.4f} EJ, Net={net:+.4f} EJ  [{status}]"
    )
    if abs(unzoned_total) >= 1e-6:
        print(f"    -> {unzoned_total:+.4f} EJ could not be assigned to a zone")
