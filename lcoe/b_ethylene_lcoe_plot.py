import os
import glob
import webbrowser

import pandas as pd
import plotly.graph_objects as go

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ID_COL = "id_LC"
TOTAL_COL = "LCOE ($/t-ethylene)"
CASE_FILE_SUFFIX = "_ethylene_case.csv"
CASE_FILE_PATTERN = f"*{CASE_FILE_SUFFIX}"

# Colors grouped by energy carrier / cost type: consumption costs use the
# saturated shade, the matching production/credit column uses a lighter tint
# of the same hue so related components read as one family in the legend.
COMPONENT_COLORS = {
    # Hydrogen — blue
    "h2_consumption":               "#1f6fb2",
    "h2_production":                "#9dc3e6",

    # Electricity — gold
    "elec_consumption":             "#d4ac0d",
    "elec_consumption - ethanol":   "#d4ac0d",
    "elec_production - ethanol":    "#f7e98e",

    # Natural gas — orange
    "natgas_consumption":           "#c0530a",
    "natgas_consumption - ethanol": "#c0530a",
    "natgas_production":            "#f0a868",

    # Biomass / ethane feedstocks — green / purple
    "biomass_consumption - ethanol": "#4f9153",
    "ethane_consumption":            "#7d3c98",

    # CO2 capture & emissions — teal (capture) / red (penalty)
    "co2captured_consumption":      "#117864",
    "modified capture cost":        "#1abc9c",
    "modified emissions cost":      "#c0392b",

    # Byproduct fuel credit
    "gasoline_production":          "#b5651d",

    # CapEx / OpEx — navy (capital) / slate (fixed) / light gray (variable)
    "investment_cost":              "#1b2631",
    "investment_cost - ethanol":    "#1b2631",
    "fixed_om_cost":                "#5d6d7e",
    "fixed_om_cost - ethanol":      "#5d6d7e",
    "variable_om_cost":             "#aeb6bf",
    "variable_om_cost - ethanol":   "#aeb6bf",
}
FALLBACK_COLOR = "#888888"


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

    fig.add_trace(go.Scatter(
        name=TOTAL_COL,
        x=df[ID_COL],
        y=df[TOTAL_COL],
        mode="markers",
        marker=dict(color="black", size=10, symbol="diamond"),
        hovertemplate="Total LCOE: %{y:.2f}<extra></extra>",
    ))

    fig.update_layout(
        barmode="relative",
        title=f"Ethylene Levelized Cost Breakdown — Scenario {label}",
        xaxis_title="Asset",
        yaxis_title="$/t-ethylene",
        xaxis=dict(categoryorder="array", categoryarray=df[ID_COL].tolist(), tickangle=-45),
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