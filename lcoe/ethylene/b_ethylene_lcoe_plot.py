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

ID_COL = "id_LC"
TOTAL_COL = "LCOE ($/t-ethylene)"
CASE_FILE_SUFFIX = "_ethylene_combined.csv"
CASE_FILE_PATTERN = f"*{CASE_FILE_SUFFIX}"

MAX_TECHNOLOGIES = None   # e.g. 40 -> keep only the 40 cheapest technologies
MAX_LCOE = 1944           # e.g. 150 -> drop technologies with LCOE above 150 $/t-ethylene

ETHANOL_LABEL_COLOR = "gold"   # x-axis tick label color for any asset id containing "ethanol"

# Flags an x-axis label with a checkmark if that asset actually shows up
# with non-negligible output in MACRO's own ethylene production results
# (the same annual_flows_balance_Ethylene.csv that ETHYLENE_Macro.py
# plots), as opposed to LCOE candidates that never get built. MACRO tracks
# "Existing"-capacity assets as a genuinely separate edge from the
# new-build one for the same code (e.g. "Existing_NE_F-NGin-H2out_..." vs
# "NE_F-NGin-H2out_..."), matching the LCOE table's own distinct
# "Existing_"-prefixed rows, and RETROFIT options now have their own
# distinct "_RETROFIT"-suffixed LCOE row too — so edge names are matched
# as-is against the LCOE table's ids, with no stripping. The 1.0-tonne
# threshold mirrors ETHYLENE_Macro.py's own noise cutoff for "active"
# categories.
PRODUCTION_EDGE_SUFFIX = "_ethylene_production_edge"
PRODUCTION_FLOW_THRESHOLD = 100000.0
PRODUCTION_CHECKMARK = " ✓"
# Bold bright yellow text, not a background highlight — Plotly's pseudo-html
# forwards arbitrary CSS into the rendered SVG <tspan>, but SVG text has no
# CSS background box, so "background-color" silently has no visual effect
# there. Bold/color do render, so that's the highlight instead. Takes
# priority over ETHANOL_LABEL_COLOR if an asset matches both rules. Uses
# the same bright yellow already in COMPONENT_COLORS (elec_production) —
# pure "#ffff00" reads as nearly invisible against a white chart background.
PRODUCTION_HIGHLIGHT_STYLE = "color:#008000;font-weight:bold"


def get_produced_edges(label):
    """Returns the set of MACRO ethylene production Edge names with non-negligible flow for this scenario."""
    scenario_path = MACRO_SCENARIO_PATHS.get(label)
    if scenario_path is None:
        return set()

    balance_path = os.path.join(
        MACRO_BASE_DIR, scenario_path,
        "annual_flow_results", "balance_specific_flows", "annual_flows_balance_Ethylene.csv",
    )
    if not os.path.exists(balance_path):
        return set()

    balance_df = pd.read_csv(balance_path)
    balance_df.columns = balance_df.columns.str.strip()
    produced = balance_df.loc[balance_df["Annual_Flow"].abs() > PRODUCTION_FLOW_THRESHOLD, "Edge"]
    return set(produced)

# Shared with b_ethanol_lcoe_plot.py so both charts read consistently. All
# feedstock consumption is green (shade varies by carrier); byproduct
# production/credits get a vivid non-green family; CapEx/OpEx is indigo.
COMPONENT_COLORS = {
    # Feedstock consumption — green family
    # Upstream combined CSVs use "- ethanol prod." in some cases and the
    # shorter "- ethanol" in others for the same cost category, so both
    # suffix variants are mapped here to the same color.
    "h2_consumption":                "#00c853",
    "elec_consumption":              "#43a047",
    "elec_consumption - ethanol prod.":    "#43a047",
    "elec_consumption - ethanol":          "#43a047",
    "biomass_consumption":           "#2e7d32",
    "biomass_consumption - ethanol prod.": "#2e7d32",
    "biomass_consumption - ethanol":       "#2e7d32",
    "natgas_consumption":            "#76d275",
    "natgas_consumption - ethanol prod.":  "#76d275",
    "natgas_consumption - ethanol":        "#76d275",
    "ethane_consumption":            "#1b5e20",
    "co2captured_consumption":       "#69f0ae",

    # Byproduct production / credits — vivid, non-green family
    "elec_production":               "#ffd600",
    "elec_production - ethanol prod.":     "#ffd600",
    "elec_production - ethanol":           "#ffd600",
    "h2_production":                 "#40c4ff",
    "natgas_production":             "#ff6e40",
    "gasoline_production":           "#ff9100",

    # CO2 capture & emissions adjustments — bright teal (capture) / red (penalty)
    "modified capture cost":         "#1de9b6",
    "modified emissions cost":       "#ff1744",

    # CapEx / OpEx — vivid indigo (capital -> dark, fixed -> medium, variable -> light)
    "investment_cost":               "#3949ab",
    "investment_cost - ethanol prod.":     "#3949ab",
    "investment_cost - ethanol":           "#3949ab",
    "fixed_om_cost":                 "#5c6bc0",
    "fixed_om_cost - ethanol prod.":       "#5c6bc0",
    "fixed_om_cost - ethanol":             "#5c6bc0",
    "variable_om_cost":              "#9fa8da",
    "variable_om_cost - ethanol prod.":    "#9fa8da",
    "variable_om_cost - ethanol":          "#9fa8da",
}
FALLBACK_COLOR = "#888888"

DEMAND_DUAL_ID = "ethylene_demand_global"
DEMAND_DUAL_COLOR = "red"
DEFAULT_MARKER_COLOR = "black"

def make_plot(csv_path):
    df = pd.read_csv(csv_path)

    exclude_ids = {DEMAND_DUAL_ID}
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

    label = os.path.basename(csv_path).removesuffix(CASE_FILE_SUFFIX)
    produced_edges = get_produced_edges(label)

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

    marker_colors = [
        DEMAND_DUAL_COLOR if id_val == DEMAND_DUAL_ID else DEFAULT_MARKER_COLOR
        for id_val in df[ID_COL]
    ]

    fig.add_trace(go.Scatter(
        name=TOTAL_COL,
        x=df[ID_COL],
        y=df[TOTAL_COL],
        mode="markers",
        marker=dict(color=marker_colors, size=10, symbol="diamond"),
        hovertemplate="Total LCOE: %{y:.2f}<extra></extra>",
    ))

    # Highlight ethanol-derived assets by recoloring their tick label text,
    # and append a checkmark for assets with actual non-negligible MACRO
    # production (via Plotly's pseudo-html span support) rather than
    # altering the bars themselves, since the bars are already colored by
    # cost component.
    tick_text = []
    for asset_id in df[ID_COL]:
        display = asset_id
        production_edge = f"{asset_id}{PRODUCTION_EDGE_SUFFIX}"
        is_produced = production_edge in produced_edges
        if is_produced:
            display = f"{display}{PRODUCTION_CHECKMARK}"
        if is_produced:
            display = f'<span style="{PRODUCTION_HIGHLIGHT_STYLE}">{display}</span>'
        elif "b-" in asset_id.lower():
            display = f'<span style="color:{ETHANOL_LABEL_COLOR}">{display}</span>'
        tick_text.append(display)

    fig.update_layout(
        barmode="relative",
        title=f"Ethylene Levelized Cost Breakdown — Scenario {label}",
        xaxis_title="Asset",
        yaxis_title="$/t-ethylene",
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

    html_path = os.path.join(SCRIPT_DIR, f"{label}_ethylene_lcoe_breakdown.html")
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