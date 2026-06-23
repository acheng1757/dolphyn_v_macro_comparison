#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

macro_conversion_factor = 3.6e-9  # MWh -> EJ

# ---------------------------------------------------------------------
# Desired order, colors, and labels (same as LF_Macro.py, minus Demand,
# Non-Served Demand, and Fossil — all three are single global nodes with
# no per-zone breakdown in this dataset)
# ---------------------------------------------------------------------

desired_order = [
    "Bio MeOH - Gasoline Non CCS",
    "Bio MeOH - Gasoline Mid CCS",
    "Bio MeOH - Gasoline High CCS",
    "Bio FT (High Jetfuel) High CCS",
    "Bio FT (High Diesel) Mid CCS",
    "Bio FT (High Diesel) High CCS",
    "Bio FT (High Diesel) Non CCS",
    "SFT Non CCS",
    "SFT CCS",
    "Ethylene Gasoline",
    "Ethanol to Gasoline",
    "Ethanol to Diesel",
    "Ethanol to JetFuel",
    "Ethanol to Diesel JetFuel",
]

category_colors = {
    "Bio MeOH - Gasoline Non CCS": "lightblue",
    "Bio MeOH - Gasoline Mid CCS": "cornflowerblue",
    "Bio MeOH - Gasoline High CCS": "royalblue",
    "Bio FT (High Jetfuel) High CCS": "chocolate",
    "Bio FT (High Diesel) Mid CCS": "limegreen",
    "Bio FT (High Diesel) High CCS": "forestgreen",
    "Bio FT (High Diesel) Non CCS": "yellowgreen",
    "SFT Non CCS": "purple",
    "SFT CCS": "indigo",
    "Ethylene Gasoline": "#e8630a",
    "Ethanol to Gasoline":      "#ffd700",
    "Ethanol to Diesel":        "#ffd700",
    "Ethanol to JetFuel":       "#ffd700",
    "Ethanol to Diesel JetFuel": "#ffd700",
}

label_map = {
    "Bio MeOH - Gasoline Non CCS": "Bio-MTG",
    "Bio MeOH - Gasoline Mid CCS": "Bio-MTG CC31",
    "Bio MeOH - Gasoline High CCS": "Bio-MTG CC99",
    "Bio FT (High Jetfuel) High CCS": "Bio-FT (Jet) CC84",
    "Bio FT (High Diesel) Mid CCS": "Bio-FT (Diesel) CC53",
    "Bio FT (High Diesel) High CCS": "Bio-FT (Diesel) CC99",
    "Bio FT (High Diesel) Non CCS": "Bio-FT (Diesel)",
    "SFT Non CCS": "Syn-FT (Jet)",
    "SFT CCS": "Syn-FT (Jet) CC99",
    "Ethylene Gasoline": "Ethylene Gasoline",
    "Ethanol to Gasoline":      "Eth. Upgrading (Gasoline)",
    "Ethanol to Diesel":        "Eth. Upgrading (Diesel)",
    "Ethanol to JetFuel":       "Eth. Upgrading (JetFuel)",
    "Ethanol to Diesel JetFuel": "Eth. Upgrading (Diesel+Jet)",
}

# ---------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------
zone_list = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]


def extract_zone(edge_name):
    """
    Pull the zone code out of a MACRO edge name.

    Production/consumption edges put the zone first:
        CEN_FT_High_Diesel_Non_CCS_Herb_diesel_edge
        TX_Ethanol_to_Diesel_diesel_production_edge

    Global/system-wide edges (Demand, Fossil Petroleum Refinery) have no
    zone and return None.
    """
    tokens = str(edge_name).split("_")
    candidates = tokens[:1]
    if tokens[:1] == ["Existing"] and len(tokens) > 1:
        candidates.append(tokens[1])
    if tokens:
        candidates.append(tokens[-1])

    for candidate in candidates:
        if candidate in zone_list:
            return candidate

    return None


# ---------------------------------------------------------------------
# MACRO liquid-fuel balance helpers (same as LF_Macro.py)
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

    if sector == "Demand" or "demand" in text:
        return "Demand"

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

        # Non-CCS High-Diesel FT: explicit "_Non_CCS_" infix for Herb/Wood
        # feedstocks, or no CCS/Non_CCS infix at all for Agri (confirmed via
        # beccs_liquid_fuels.json: <zone>_FT_High_Diesel_Agri has no suffix,
        # alongside its own _CCS_53_Agri/_CCS_99_Agri siblings — the bare id
        # is Agri's non-CCS option). Once 99/53 are ruled out above, any
        # remaining "high_diesel" match is non-CCS by elimination.
        if "high_diesel" in text:
            return "Bio FT (High Diesel) Non CCS"

        if "high_jetfuel" in text:
            return "Bio FT (High Jetfuel) High CCS"

        return None

    if category == "Fossil Liquid Fuels":
        return None

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
# Ethanol-to-X production, by zone
# ---------------------------------------------------------------------
# Ethanol_to_X assets are tagged as "Transmission" in Step 1, so they are
# absent from the Liquid_Fuels balance file. We pull their LF output edges
# from the all_nonzero file, one category per process, grouped by zone.
# Diesel_JetFuel must be matched before plain Diesel to avoid overlap.

_LF_PROD_EDGES = (
    "gasoline_production_edge",
    "diesel_production_edge",
    "jetfuel_production_edge",
)

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


def _load_ethanol_upgrading_by_process_by_zone(results_dir):
    """Return {plot_category: {zone: annual_flow_MWh}} for each Ethanol_to_X process."""
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
            df["Edge"].str.endswith(_LF_PROD_EDGES)
        )
        if exclude is not None:
            mask &= ~df["Edge"].str.contains(exclude, na=False)
        result[cat] = flows[mask].groupby(zones[mask]).sum().to_dict()
    return result


# ---------------------------------------------------------------------
# Read MACRO liquid-fuel balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
system_level_totals_by_scenario = {}

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

    macro_lf["Annual_Flow"] = (
        pd.to_numeric(macro_lf["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * macro_conversion_factor
    )

    macro_lf["Plot_Category"] = macro_lf.apply(map_macro_lf_category, axis=1)
    macro_lf = macro_lf[macro_lf["Plot_Category"].isin(desired_order)].copy()

    # System-level total: the same aggregate LF_Macro.py would show for
    # these categories, used as the "all zone" reference below. The
    # Ethanol-to-X categories are added in afterwards from the separate
    # all_nonzero file, same as LF_Macro.py does.
    system_level_total = (
        macro_lf.groupby("Plot_Category")["Annual_Flow"].sum()
        .reindex(desired_order)
        .fillna(0.0)
    )
    upgrading_totals = _load_ethanol_upgrading_by_process(results_dir)
    for cat in ["Ethanol to Gasoline", "Ethanol to Diesel", "Ethanol to JetFuel", "Ethanol to Diesel JetFuel"]:
        system_level_total[cat] = upgrading_totals.get(cat, 0.0) * macro_conversion_factor
    system_level_totals_by_scenario[scen_short] = system_level_total

    macro_lf["Zone"] = macro_lf["Edge"].apply(extract_zone)
    macro_lf_zoned = macro_lf[macro_lf["Zone"].notna()].copy()

    zone_table = (
        macro_lf_zoned
        .groupby(["Zone", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .reindex(zone_list)
        .fillna(0.0)
    )

    for col in desired_order:
        if col not in zone_table.columns:
            zone_table[col] = 0.0

    upgrading_by_zone = _load_ethanol_upgrading_by_process_by_zone(results_dir)
    for cat in ["Ethanol to Gasoline", "Ethanol to Diesel", "Ethanol to JetFuel", "Ethanol to Diesel JetFuel"]:
        zone_vals = upgrading_by_zone.get(cat, {})
        for zone, raw_flow in zone_vals.items():
            if zone in zone_table.index:
                zone_table.loc[zone, cat] = raw_flow * macro_conversion_factor

    zone_table = zone_table[desired_order]
    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nLiquid fuels production by zone — Scenario {scen_short} (EJ):")
    print(zone_table)


# ---------------------------------------------------------------------
# Plot — Plotly only, one subplot per scenario, zones as horizontal bars
# ---------------------------------------------------------------------

plotted_scenarios = [s for s in scenario_names if s in zone_tables_by_scenario]

active_cols = [
    col for col in desired_order
    if any(
        zone_tables_by_scenario[s][col].abs().sum() > 1e-6
        for s in plotted_scenarios
    )
]

fig_plotly = make_subplots(
    rows=len(plotted_scenarios),
    cols=1,
    shared_xaxes=True,
    subplot_titles=[f"Scenario {s}" for s in plotted_scenarios],
    vertical_spacing=0.4 / len(plotted_scenarios) if len(plotted_scenarios) > 1 else 0.1,
)

legend_shown = set()

for row_idx, scen in enumerate(plotted_scenarios, start=1):
    plot_df = zone_tables_by_scenario[scen][active_cols]

    for col in active_cols:
        fig_plotly.add_trace(
            go.Bar(
                name=label_map.get(col, col),
                y=zone_list,
                x=plot_df[col].tolist(),
                orientation="h",
                marker_color=category_colors.get(col, "#333333"),
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

fig_plotly.update_layout(
    barmode="relative",
    title="Liquid Fuels Production by Zone (EJ)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="EJ", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "lf_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Coverage check: by-zone grand total vs. the system-level ("all zone") total
# for the same categories, computed from the identical source rows. Demand
# and Fossil are excluded from both sides since they're single global nodes
# with no zone to assign.
# ---------------------------------------------------------------------------
print("\nLiquid Fuels by-zone balance check:")
for scen in plotted_scenarios:
    zoned_total = zone_tables_by_scenario[scen][active_cols].to_numpy().sum()
    system_total = system_level_totals_by_scenario[scen][active_cols].sum()
    diff = zoned_total - system_total
    status = "OK" if abs(diff) < 1e-6 else "MISMATCH"
    print(
        f"  Scenario {scen}: By-zone total={zoned_total:+.4f} EJ, "
        f"System-level total={system_total:+.4f} EJ, "
        f"Diff={diff:+.6f} EJ  [{status}]"
    )
