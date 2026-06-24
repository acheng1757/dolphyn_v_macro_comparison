import os
import glob
import webbrowser

import pandas as pd
import plotly.graph_objects as go

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ID_COL = "id"
TOTAL_COL = "LCOE ($/MWh-ethanol)"
CASE_FILE_SUFFIX = "_ethanol_combined.csv"
CASE_FILE_PATTERN = f"*{CASE_FILE_SUFFIX}"

# Shared with b_ethylene_lcoe_plot.py so both charts read consistently. All
# feedstock consumption is green (shade varies by carrier); byproduct
# production/credits get a vivid non-green family; CapEx/OpEx is indigo.
COMPONENT_COLORS = {
    # Feedstock consumption — green family
    "h2_consumption":                "#00c853",
    "elec_consumption":              "#43a047",
    "elec_consumption - ethanol":    "#43a047",
    "biomass_consumption":           "#2e7d32",
    "biomass_consumption - ethanol": "#2e7d32",
    "natgas_consumption":            "#76d275",
    "natgas_consumption - ethanol":  "#76d275",
    "ethane_consumption":            "#1b5e20",
    "co2captured_consumption":       "#69f0ae",

    # Byproduct production / credits — vivid, non-green family
    "elec_production":               "#ffd600",
    "elec_production - ethanol":     "#ffd600",
    "h2_production":                 "#40c4ff",
    "natgas_production":             "#ff6e40",
    "gasoline_production":           "#ff9100",

    # CO2 capture & emissions adjustments — bright teal (capture) / red (penalty)
    "modified capture cost":         "#1de9b6",
    "modified emissions cost":       "#ff1744",

    # CapEx / OpEx — vivid indigo (capital -> dark, fixed -> medium, variable -> light)
    "investment_cost":               "#3949ab",
    "investment_cost - ethanol":     "#3949ab",
    "fixed_om_cost":                 "#5c6bc0",
    "fixed_om_cost - ethanol":       "#5c6bc0",
    "variable_om_cost":              "#9fa8da",
    "variable_om_cost - ethanol":    "#9fa8da",
}
FALLBACK_COLOR = "#888888"

DEMAND_DUAL_ID = "ethanol_demand_global"
DEMAND_DUAL_COLOR = "red"
DEFAULT_MARKER_COLOR = "black"


def make_plot(csv_path):
    df = pd.read_csv(csv_path)

    # Columns C:V (component cost/consumption columns): everything except the
    # source tracker, the id, and the total LCOE column.
    component_cols = [c for c in df.columns if c not in ("source_file", ID_COL, TOTAL_COL)]
    component_cols = [c for c in component_cols if df[c].notna().any()]

    label = os.path.basename(csv_path).removesuffix(CASE_FILE_SUFFIX)

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

    fig.update_layout(
        barmode="relative",
        title=f"Ethanol Levelized Cost Breakdown — Scenario {label}",
        xaxis_title="Asset",
        yaxis_title="$/MWh-ethanol",
        xaxis=dict(categoryorder="array", categoryarray=df[ID_COL].tolist(), tickangle=-45),
        legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
        height=650,
        margin=dict(b=160),
    )

    html_path = os.path.join(SCRIPT_DIR, f"{label}_ethanol_lcoe_breakdown.html")
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