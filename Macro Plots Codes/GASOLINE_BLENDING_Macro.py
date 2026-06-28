import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths, load_annual_nsd

pd.set_option("display.max_columns", None)
plt.rcParams["font.family"] = "Arial"

MWH_TO_EJ = 3.6e-9

# ---------------------------------------------------------------------
# The Global_Gasoline_Blending asset blends raw Ethanol and Gasoline into
# Blended_Gasoline, which is what satisfies Gasoline_MW_Global demand.
# Demand here is the blended-fuel requirement; production is the two raw
# commodity inflows that get blended together (different commodities, but
# shown side by side since that's what blending means).
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Non-Served Demand",
    "Ethanol",
    "Gasoline",
]

category_colors = {
    "Demand": "bisque",
    "Non-Served Demand": "red",
    "Ethanol": "#ffd700",
    "Gasoline": "steelblue",
}

category_names = {
    "Demand": "Demand",
    "Non-Served Demand": "Non-Served Demand",
    "Ethanol": "Ethanol",
    "Gasoline": "Gasoline",
}

# ---------------------------------------------------------------------
# Read MACRO Gasoline_MW_Global demand from the Liquid Fuels balance file
# ---------------------------------------------------------------------

macro_combined_data = pd.DataFrame(0.0, index=scenario_names, columns=desired_order)

for scen_short, scen_path in macro_scenario_paths.items():
    lf_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Liquid_Fuels.csv",
    )

    if not os.path.exists(lf_path):
        print(f"Warning: MACRO liquid-fuels balance file not found: {lf_path}")
        continue

    macro_lf = pd.read_csv(lf_path)
    macro_lf.columns = macro_lf.columns.str.strip()

    required_cols = ["Edge", "Annual_Flow"]
    missing_cols = [c for c in required_cols if c not in macro_lf.columns]
    if missing_cols:
        raise ValueError(
            f"{lf_path} is missing required columns: {missing_cols}. "
            f"Available columns are: {macro_lf.columns.tolist()}"
        )

    flows = pd.to_numeric(macro_lf["Annual_Flow"], errors="coerce").fillna(0.0)
    demand_flow = flows[macro_lf["Edge"] == "Gasoline_MW_Global"].sum()

    if scen_short in macro_combined_data.index:
        macro_combined_data.loc[scen_short, "Demand"] = demand_flow * MWH_TO_EJ


# ---------------------------------------------------------------------
# Read the blending asset's Ethanol and Gasoline inflows (production side)
# ---------------------------------------------------------------------
# Global_Gasoline_Blending_ethanol_edge / _gasoline_edge aren't classified
# by Step 1 (Sector/Category = NA), so pull them directly from the
# all_nonzero file. Both are negative (consumption into blending) — negate
# so they plot as positive bars feeding the blend, same convention as Demand.

def _load_blending_inflows(results_dir):
    """Return {'Ethanol': MWh, 'Gasoline': MWh} flowing into Global_Gasoline_Blending."""
    path = os.path.join(
        results_dir,
        "annual_flow_results",
        "all_nonzero_annual_flows_with_categories.csv",
    )
    result = {"Ethanol": 0.0, "Gasoline": 0.0}
    if not os.path.exists(path):
        return result
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    if "Edge" not in df.columns or "Annual_Flow" not in df.columns:
        return result
    flows = pd.to_numeric(df["Annual_Flow"], errors="coerce").fillna(0.0)
    ethanol_flow = flows[df["Edge"] == "Global_Gasoline_Blending_ethanol_edge"].sum()
    gasoline_flow = flows[df["Edge"] == "Global_Gasoline_Blending_gasoline_edge"].sum()
    result["Ethanol"] = -ethanol_flow
    result["Gasoline"] = -gasoline_flow
    return result


for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    inflows = _load_blending_inflows(results_dir)
    if scen_short in macro_combined_data.index:
        for cat, raw_flow in inflows.items():
            macro_combined_data.loc[scen_short, cat] = raw_flow * MWH_TO_EJ


# ---------------------------------------------------------------------
# Non-served demand
# ---------------------------------------------------------------------

for scen_short, scen_path in macro_scenario_paths.items():
    if scen_short in macro_combined_data.index:
        nsd = load_annual_nsd(scen_path, "gasoline_blended_demand") * MWH_TO_EJ
        macro_combined_data.loc[scen_short, "Non-Served Demand"] = nsd

macro_combined_data = macro_combined_data.reindex(scenario_names).fillna(0.0)[desired_order]


# ---------------------------------------------------------------------
# Print balance table for checking
# ---------------------------------------------------------------------

print("\nMACRO gasoline blending balance by scenario (EJ):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Gasoline Blending balance check:")
for scen in macro_combined_data.index:
    row = macro_combined_data.loc[scen]
    total_positive = row[row > 0].sum()
    total_negative = row[row < 0].sum()
    net = total_positive + total_negative
    status = "✓ BALANCED" if abs(net) < 0.01 else "✗ IMBALANCE"
    print(
        f"  {scen}: Supply={total_positive:+.4f} EJ, "
        f"Demand={total_negative:+.4f} EJ, "
        f"Net={net:+.4f} EJ  [{status}]"
    )

# ---------------------------------------------------------------------
# Plot MACRO-only gasoline blending balance
# ---------------------------------------------------------------------

plot_df = macro_combined_data[desired_order].copy()

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
ax.set_title("Gasoline Blending Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

_pos_ext = plot_df.clip(lower=0).sum(axis=1).max()
_neg_ext = plot_df.clip(upper=0).sum(axis=1).min()
_pad = max(abs(_pos_ext), abs(_neg_ext)) * 0.12 or 1.0
ax.set_xlim(_neg_ext - _pad, _pos_ext + _pad)
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

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

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.34)

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
        hovertemplate='%{fullData.name}: %{x:.4f} EJ<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Gasoline Blending Balance (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gasoline_blending_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')
