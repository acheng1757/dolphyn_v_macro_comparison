import ast
import os
import glob
import webbrowser

import pandas as pd
import plotly.graph_objects as go

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STEP_1_PATH = os.path.join(SCRIPT_DIR, "..", "..", "Step_1_Process_Macro_Flows_and_Balance_Demand.py")


def _load_step1_scenario_config(step1_path):
    """
    Reads macro_base_dir/_scenarios straight out of Step_1's source via AST
    (rather than importing it) because importing that module runs its full
    MACRO processing pipeline as a side effect — too slow for a plot script
    that's re-run often. Mirrors Step_1's own
    `macro_scenario_paths = {label: path for label, path, _ in _scenarios}`,
    so whichever scenarios are currently uncommented there are what show up
    here automatically.
    """
    tree = ast.parse(open(step1_path).read(), filename=step1_path)

    base_dir = None
    scenarios = None
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id == "macro_base_dir":
            base_dir = ast.literal_eval(node.value)
        elif node.targets[0].id == "_scenarios":
            scenarios = ast.literal_eval(node.value)

    if base_dir is None or scenarios is None:
        raise RuntimeError(f"Could not find macro_base_dir/_scenarios in {step1_path}")

    return base_dir, {label: path for label, path, _ in scenarios}


MACRO_BASE_DIR, MACRO_SCENARIO_PATHS = _load_step1_scenario_config(STEP_1_PATH)

MAX_TECHNOLOGIES = 50   # e.g. 40 -> keep only the 40 cheapest technologies
MAX_LCOE = None          # e.g. 150 -> drop technologies with LCOE above 150 $/MWh-fuel

ETHANOL_LABEL_COLOR = "gold"   # x-axis tick label color for any asset id containing "ethanol"

ID_COL = "id_LC"
TOTAL_COL = "LCOE ($/MWh-fuel)"
CASE_FILE_SUFFIX = "_lf_combined.csv"
CASE_FILE_PATTERN = f"*{CASE_FILE_SUFFIX}"

# Shared with b_ethanol_lcoe_plot.py so both charts read consistently. All
# feedstock consumption is green (shade varies by carrier); byproduct
# production/credits get a vivid non-green family; CapEx/OpEx is indigo.
COMPONENT_COLORS = {
    # Feedstock consumption — green family
    "h2_consumption":                "#00c853",
    "elec_consumption":              "#43a047",
    "elec_consumption - ethanol prod.":    "#43a047",
    "biomass_consumption":           "#2e7d32",
    "biomass_consumption - ethanol prod.": "#2e7d32",
    "natgas_consumption":            "#76d275",
    "natgas_consumption - ethanol prod.":  "#76d275",

    # Byproduct production / credits — vivid, non-green family
    "elec_production":               "#ffd600",
    "elec_production - ethanol prod.":     "#ffd600",
    "h2_production":                 "#40c4ff",
    "natgas_production":             "#ff6e40",

    # CO2 capture & emissions adjustments — bright teal (capture) / red (penalty)
    "modified capture cost":         "#1de9b6",
    "modified emissions cost":       "#ff1744",

    # CapEx / OpEx — vivid indigo (capital -> dark, fixed -> medium, variable -> light)
    "investment_cost":               "#3949ab",
    "investment_cost - ethanol prod.":     "#3949ab",
    "fixed_om_cost":                 "#5c6bc0",
    "fixed_om_cost - ethanol prod.":       "#5c6bc0",
    "variable_om_cost":              "#9fa8da",
    "variable_om_cost - ethanol prod.":    "#9fa8da",

    # Manually-provided fossil benchmark cost — brown, distinct from model components
    "fossil_fuel_cost":              "#5d4037",
}
FALLBACK_COLOR = "#888888"

DEMAND_DUAL_IDS = ["gasoline_demand_global", "diesel_demand_global", "jetfuel_demand_global"]
DEMAND_DUAL_COLORS = {
    "gasoline_demand_global": "#e53935",  # red
    "diesel_demand_global":   "#8e24aa",  # purple
    "jetfuel_demand_global":  "#1565c0",  # blue
}
DEFAULT_MARKER_COLOR = "black"

FOSSIL_FUEL_COST = {
    "fossil_gasoline": 69.57358456,
    "fossil_diesel":   92.81027464,
    "fossil_jetfuel":  70.56310587,
}
FOSSIL_CO2_CONTENT = {  # t-CO2/MWh-fuel
    "fossil_gasoline": 0.243968185,
    "fossil_diesel":   0.249427613,
    "fossil_jetfuel":  0.246356685,
}

# Flags an x-axis label with a checkmark + bold bright-yellow highlight if
# that asset actually shows up with non-negligible output in MACRO's own
# annual_flows_balance_Liquid_Fuels.csv. Unlike the ethylene plot, ids here
# match the balance edges directly (no Existing_/RETROFIT handling needed),
# but a single asset can co-produce multiple fuels, so its edge name is
# id_LC + one of several possible fuel-specific suffixes (e.g. Bioenergy
# assets use "_diesel_edge"/"_jetfuel_edge"/"_gasoline_edge", Ethanol
# Upgrading assets use "_diesel_production_edge"/"_gasoline_production_edge").
# Suffixes are matched as an exact full-string set (not a startswith scan)
# because some ids are themselves prefixes of other ids (e.g.
# "NW_Ethanol_to_Gasoline" vs "NW_Ethanol_to_Gasoline_Diesel") and a prefix
# scan would cross-attribute one asset's edges to the other.
PRODUCTION_EDGE_SUFFIXES = (
    "_gasoline_edge", "_diesel_edge", "_jetfuel_edge",
    "_gasoline_production_edge", "_diesel_production_edge", "_jetfuel_production_edge",
)
PRODUCTION_FLOW_THRESHOLD = 1.0
PRODUCTION_CHECKMARK = " ✓"
PRODUCTION_HIGHLIGHT_STYLE = "color:#008000;font-weight:bold"


def get_produced_edges(label):
    """Returns the set of MACRO liquid-fuels production Edge names with non-negligible flow for this scenario."""
    scenario_path = MACRO_SCENARIO_PATHS.get(label)
    if scenario_path is None:
        return set()

    balance_path = os.path.join(
        MACRO_BASE_DIR, scenario_path,
        "annual_flow_results", "balance_specific_flows", "annual_flows_balance_Liquid_Fuels.csv",
    )
    if not os.path.exists(balance_path):
        return set()

    balance_df = pd.read_csv(balance_path)
    balance_df.columns = balance_df.columns.str.strip()
    return set(
        balance_df.loc[balance_df["Annual_Flow"].abs() > PRODUCTION_FLOW_THRESHOLD, "Edge"]
    )


def get_co2_sink_dual(label):
    """Returns the case's co2_sink shadow price ($/t-CO2) from co2_cap_duals.csv."""
    scenario_path = MACRO_SCENARIO_PATHS.get(label)
    if scenario_path is None:
        return None

    co2_duals_path = os.path.join(MACRO_BASE_DIR, scenario_path, "co2_cap_duals.csv")
    if not os.path.exists(co2_duals_path):
        return None

    co2_df = pd.read_csv(co2_duals_path)
    co2_sink_value = co2_df.loc[co2_df["Node"] == "co2_sink", "CO2_Shadow_Price"].values
    return round(float(co2_sink_value[0]), 6) if len(co2_sink_value) > 0 else None


def make_plot(csv_path):
    df = pd.read_csv(csv_path)
    label = os.path.basename(csv_path).removesuffix(CASE_FILE_SUFFIX)
    produced_edges = get_produced_edges(label)

    co2_sink = get_co2_sink_dual(label)
    if co2_sink is None:
        print(f"  WARNING: could not find co2_sink dual for case {label}; omitting fossil benchmarks")
    else:
        fossil_rows = []
        for fossil_id, base_cost in FOSSIL_FUEL_COST.items():
            emissions_cost = FOSSIL_CO2_CONTENT[fossil_id] * co2_sink
            fossil_rows.append({
                ID_COL: fossil_id,
                "fossil_fuel_cost": base_cost,
                "modified emissions cost": emissions_cost,
                TOTAL_COL: base_cost + emissions_cost,
            })
        df = pd.concat([df, pd.DataFrame(fossil_rows)], ignore_index=True)
        df = df.sort_values(TOTAL_COL, ascending=True, na_position="last").reset_index(drop=True)

    exclude_ids = set(FOSSIL_FUEL_COST) | set(DEMAND_DUAL_IDS)
    is_technology = ~df[ID_COL].isin(exclude_ids)

    if MAX_LCOE is not None:
        drop = is_technology & (df[TOTAL_COL] > MAX_LCOE)
        df = df.loc[~drop].reset_index(drop=True)
        is_technology = ~df[ID_COL].isin(exclude_ids)

    if MAX_TECHNOLOGIES is not None:
        tech_keep_ids = df.loc[is_technology].nsmallest(MAX_TECHNOLOGIES, TOTAL_COL)[ID_COL]
        keep = ~is_technology | df[ID_COL].isin(tech_keep_ids)
        df = df.loc[keep].reset_index(drop=True)

    df = df.sort_values(TOTAL_COL, ascending=True, na_position="last").reset_index(drop=True)

    # Columns C:V (component cost/consumption columns): everything except the
    # source tracker, the id, and the total LCOE column.
    component_cols = [c for c in df.columns if c not in ("source_file", ID_COL, TOTAL_COL)]
    component_cols = [c for c in component_cols if df[c].notna().any()]

    fig = go.Figure()

    for col in component_cols:
        color = COMPONENT_COLORS.get(col)
        if color is None:
            print(f"  WARNING: no color mapping for column '{col}'; using fallback gray")
            color = FALLBACK_COLOR
        fig.add_trace(go.Bar(
            name=col,
            x=df[ID_COL],
            y=df[col].fillna(0),
            marker_color=color,
            hovertemplate=f"{col}: " + "%{y:.2f}<extra></extra>",
        ))

    is_dual = df[ID_COL].isin(DEMAND_DUAL_IDS)

    fig.add_trace(go.Scatter(
        name=TOTAL_COL,
        x=df.loc[~is_dual, ID_COL],
        y=df.loc[~is_dual, TOTAL_COL],
        mode="markers",
        marker=dict(color=DEFAULT_MARKER_COLOR, size=10, symbol="diamond"),
        hovertemplate="Total LCOE: %{y:.2f}<extra></extra>",
    ))

    for dual_id in DEMAND_DUAL_IDS:
        dual_rows = df[df[ID_COL] == dual_id]
        if dual_rows.empty:
            continue
        color = DEMAND_DUAL_COLORS.get(dual_id, DEFAULT_MARKER_COLOR)
        fig.add_trace(go.Scatter(
            name=dual_id,
            x=dual_rows[ID_COL],
            y=dual_rows[TOTAL_COL],
            mode="markers",
            marker=dict(color=color, size=10, symbol="diamond"),
            hovertemplate=f"{dual_id}: " + "%{y:.2f}<extra></extra>",
        ))

    # Highlight ethanol-derived assets by recoloring their tick label text,
    # and append a checkmark + bold bright-yellow highlight for assets with
    # actual non-negligible MACRO production (via Plotly's pseudo-html span
    # support) rather than altering the bars themselves, since the bars are
    # already colored by cost component.
    tick_text = []
    for asset_id in df[ID_COL]:
        display = asset_id
        is_produced = any(
            f"{asset_id}{suffix}" in produced_edges for suffix in PRODUCTION_EDGE_SUFFIXES
        )
        if is_produced:
            display = f"{display}{PRODUCTION_CHECKMARK}"
        if is_produced:
            display = f'<span style="{PRODUCTION_HIGHLIGHT_STYLE}">{display}</span>'
        elif "ethanol" in asset_id.lower():
            display = f'<span style="color:{ETHANOL_LABEL_COLOR}">{display}</span>'
        tick_text.append(display)

    fig.update_layout(
        barmode="relative",
        title=f"LF Levelized Cost Breakdown — Scenario {label}",
        xaxis_title="Asset",
        yaxis_title="$/MWh-fuel",
        xaxis=dict(
            categoryorder="array",
            categoryarray=df[ID_COL].tolist(),
            tickangle=-45,
            tickmode="array",
            tickvals=df[ID_COL].tolist(),
            ticktext=tick_text,
        ),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
        height=650,
        margin=dict(b=160),
    )

    html_path = os.path.join(SCRIPT_DIR, f"{label}_lf_lcoe_breakdown.html")
    fig.write_html(html_path)
    print(f"Wrote {html_path}")
    webbrowser.open(f"file://{html_path}")


def main():
    csv_paths = sorted(glob.glob(os.path.join(SCRIPT_DIR, CASE_FILE_PATTERN)))
    if not csv_paths:
        print(f"No files matching '{CASE_FILE_PATTERN}' found in {SCRIPT_DIR}")
        return

    for csv_path in csv_paths:
        make_plot(csv_path)


if __name__ == "__main__":
    main()