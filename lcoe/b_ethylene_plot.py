import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Input Excel file and sheet
FILE_PATH = r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/lc_summary_combined.xlsx"
SHEET = "lc_summary_seq"          # Options: "lc_summary_seq" or "lc_summary_noseq"

# Data filtering options
SORT_BY_LCOE = True
SOURCE_FILTER = None              # Example: "LCOE_SC_ESC_Ethylene.xlsx"
EXCLUDE_ZERO_LCOE = True
MAX_ROWS = None
X_LABEL = "$/GJ-ethylene"

# ── OUTPUT DIRECTORY ──────────────────────────────────────────────────────────
# Set your desired output directory here
OUTPUT_DIR = Path(
    r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots"
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Optional dynamic naming based on sheet and source
suffix = SHEET
if SOURCE_FILTER:
    suffix += "_" + Path(SOURCE_FILTER).stem

PLOTLY_HTML_OUT = OUTPUT_DIR / f"lcoe_chart_{suffix}.html"
MATPLOTLIB_PNG_OUT = OUTPUT_DIR / f"lcoe_chart_{suffix}.png"
MATPLOTLIB_DPI = 180

# ── COLOR DICTIONARY ──────────────────────────────────────────────────────────
COMPONENT_COLORS = {
    "investment_cost":              "#3b82f6",
    "fixed_om_cost":                "#3b82f6",
    "variable_om_cost":             "#9fc5e8",
    "modified capture cost":        "lightcoral",
    "modified emissions cost":      "paleturquoise",
    "co2captured_consumption":      "lightcoral",
    "h2_consumption":               "greenyellow",
    "elec_consumption":             "aqua",
    "elec_consumption - ethanol":   "mediumturquoise",
    "elec_production - ethanol":    "mediumturquoise",
    "biomass_consumption - ethanol": "green",
    "natgas_consumption":           "red",
    "natgas_consumption - ethanol": "darkred",
    "investment_cost - ethanol":    "#1e40af",
    "fixed_om_cost - ethanol":      "#1e40af",
    "variable_om_cost - ethanol":   "#3b82f6",
    "ethane_consumption":           "salmon",
    "natgas_production":            "#15803d",
    "h2_production":                "greenyellow",
    "gasoline_production":          "#7c3aed",
}

# Human-readable labels for the legend
COMPONENT_LABELS = {
    "investment_cost":              "Investment cost",
    "fixed_om_cost":                "Fixed O&M",
    "variable_om_cost":             "Variable O&M",
    "modified capture cost":        "Capture cost",
    "modified emissions cost":      "Emissions cost",
    "h2_consumption":               "H₂ consumption",
    "elec_consumption":             "Electricity",
    "elec_consumption - ethanol":   "Electricity (ethanol)",
    "elec_production - ethanol":    "Elec. production (ethanol)",
    "biomass_consumption - ethanol":"Biomass (ethanol)",
    "natgas_consumption":           "Nat. gas consumption",
    "natgas_consumption - ethanol": "Nat. gas (ethanol)",
    "investment_cost - ethanol":    "Investment (ethanol)",
    "fixed_om_cost - ethanol":      "Fixed O&M (ethanol)",
    "variable_om_cost - ethanol":   "Variable O&M (ethanol)",
    "ethane_consumption":           "Ethane",
    "natgas_production":            "Nat. gas production",
    "h2_production":                "H₂ production",
    "gasoline_production":          "Gasoline production",
    "co2captured_consumption":      "CO₂ captured",
}

# LCOE marker styling
LCOE_DOT_COLOR = "#111111"
LCOE_DOT_SIZE_PX = 8
LCOE_DOT_SIZE_PL = 10

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def load_data(file_path, sheet, source_filter, exclude_zero, sort_by_lcoe, max_rows):
    """Load and filter the dataset."""
    df = pd.read_excel(file_path, sheet_name=sheet)

    if source_filter:
        df = df[df["source_file"] == source_filter]

    if exclude_zero and "LCOE ($/GJ-ethylene)" in df.columns:
        df = df[df["LCOE ($/GJ-ethylene)"] > 0]

    if sort_by_lcoe and "LCOE ($/GJ-ethylene)" in df.columns:
        df = df.sort_values("LCOE ($/GJ-ethylene)", ascending=True)

    if max_rows:
        df = df.head(max_rows)

    return df.reset_index(drop=True)


def get_active_components(df):
    """Return component columns that contain non-zero values."""
    active = []
    for col in COMPONENT_COLORS:
        if col in df.columns and df[col].abs().max() > 1e-4:
            active.append(col)
    return active


def split_pos_neg(series):
    """Split a series into positive and negative components."""
    pos = series.clip(lower=0)
    neg = series.clip(upper=0)
    return pos, neg


# ─────────────────────────────────────────────────────────────────────────────
# Plotly Visualization
# ─────────────────────────────────────────────────────────────────────────────

def plot_plotly(df, active_comps):
    techs = df["id_LC"].tolist()
    lcoe = df["LCOE ($/GJ-ethylene)"].tolist()
    n = len(techs)

    traces = []
    for col in active_comps:
        vals = df[col].fillna(0).values
        pos, neg = split_pos_neg(pd.Series(vals))

        color = COMPONENT_COLORS[col]
        label = COMPONENT_LABELS.get(col, col)

        hover_pos = [
            f"<b>{label}</b><br>+{v:.2f} {X_LABEL}" if v > 0 else None
            for v in vals
        ]
        hover_neg = [
            f"<b>{label}</b><br>{v:.2f} {X_LABEL}" if v < 0 else None
            for v in vals
        ]

        # Positive bars
        traces.append(go.Bar(
            name=label,
            y=techs,
            x=pos.tolist(),
            orientation="h",
            marker_color=color,
            legendgroup=col,
            showlegend=True,
            hovertext=hover_pos,
            hoverinfo="text",
        ))

        # Negative bars (no duplicate legend entry)
        traces.append(go.Bar(
            name=label,
            y=techs,
            x=neg.tolist(),
            orientation="h",
            marker_color=color,
            legendgroup=col,
            showlegend=False,
            hovertext=hover_neg,
            hoverinfo="text",
        ))

    # LCOE marker
    traces.append(go.Scatter(
        name="LCOE ($/GJ)",
        y=techs,
        x=lcoe,
        mode="markers",
        marker=dict(color=LCOE_DOT_COLOR, size=LCOE_DOT_SIZE_PL),
        hovertemplate="<b>%{y}</b><br>LCOE: %{x:.2f} $/GJ<extra></extra>",
    ))

    # Prevent legend overlap
    items_per_row = 6
    legend_items = len(active_comps) + 1
    legend_rows = int(np.ceil(legend_items / items_per_row))
    top_margin = 80 + legend_rows * 30

    row_height = 28
    fig_height = max(500, n * row_height + 150)

    fig = go.Figure(data=traces)
    fig.update_layout(
        barmode="relative",
        height=fig_height,
        margin=dict(l=20, r=20, t=top_margin, b=60),
        xaxis=dict(
            title=X_LABEL,
            zeroline=True,
            zerolinecolor="rgba(0,0,0,0.25)",
            zerolinewidth=1.5,
            gridcolor="rgba(0,0,0,0.07)",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=11),
            gridcolor="rgba(0,0,0,0.05)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            traceorder="normal",
            entrywidth=120,
            entrywidthmode="pixels",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.write_html(str(PLOTLY_HTML_OUT), config={"responsive": True})
    print(f"Plotly chart saved → {PLOTLY_HTML_OUT}")
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Matplotlib Visualization
# ─────────────────────────────────────────────────────────────────────────────

def plot_matplotlib(df, active_comps):
    techs = df["id_LC"].tolist()
    lcoe = df["LCOE ($/GJ-ethylene)"].values
    n = len(techs)
    y = np.arange(n)

    fig, ax = plt.subplots(figsize=(13, max(6, n * 0.32 + 2.5)))
    legend_handles = []

    for col in active_comps:
        vals = df[col].fillna(0).values
        pos, neg = split_pos_neg(pd.Series(vals))
        color = COMPONENT_COLORS[col]
        label = COMPONENT_LABELS.get(col, col)

        ax.barh(y, pos.values, height=0.75, color=color, linewidth=0)
        ax.barh(y, neg.values, height=0.75, color=color, linewidth=0)
        legend_handles.append(mpatches.Patch(color=color, label=label))

    ax.scatter(
        lcoe, y,
        color=LCOE_DOT_COLOR,
        s=LCOE_DOT_SIZE_PX ** 2,
        zorder=5,
        label="LCOE ($/GJ)",
    )
    legend_handles.append(
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor=LCOE_DOT_COLOR,
                   markersize=LCOE_DOT_SIZE_PX,
                   label="LCOE ($/GJ)")
    )

    ax.set_yticks(y)
    ax.set_yticklabels(techs, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel(X_LABEL, fontsize=10)
    ax.set_title(f"LCOE breakdown — {SHEET}", fontsize=12, pad=20)
    ax.axvline(0, color="black", linewidth=0.8, alpha=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color="grey", alpha=0.15, linewidth=0.7)

    # Legend on top
    ncol = min(4, len(legend_handles))
    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=ncol,
        fontsize=8,
        frameon=False,
    )

    #plt.tight_layout(rect=[0, 0, 1, 0.95])
    #fig.savefig(str(MATPLOTLIB_PNG_OUT), dpi=MATPLOTLIB_DPI, bbox_inches="tight")
    #print(f"Matplotlib chart saved → {MATPLOTLIB_PNG_OUT}")
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading {FILE_PATH} / {SHEET} ...")

    df = load_data(
        file_path=FILE_PATH,
        sheet=SHEET,
        source_filter=SOURCE_FILTER,
        exclude_zero=EXCLUDE_ZERO_LCOE,
        sort_by_lcoe=SORT_BY_LCOE,
        max_rows=MAX_ROWS,
    )
    print(f"  {len(df)} rows after filtering.")

    if df.empty:
        print("No data available for plotting.")
        return

    active = get_active_components(df)
    print(f"  {len(active)} active cost components: {active}")

    plot_plotly(df, active)
    plot_matplotlib(df, active)


if __name__ == "__main__":
    main()