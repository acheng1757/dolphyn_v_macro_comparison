#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
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

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Desired order, colors, and labels (same styling as ETHYLENE_Macro.py)
# ---------------------------------------------------------------------

desired_order = [
    "Existing TSC:H2",
    "Ret-TSC:H2",
    "Ret-TSC",
    "Ret-TSC+CC90",
    "Ret-TSC+CC90:H2",
    "Ret-TSC+H2in",
    "Ret-TSC+CC90+H2in",
    "Ret-ESC",
    "Ret-TSC+H2in:CH4",

    "TSC:H2",
    "TSC",
    "TSC+CC90",
    "TSC+CC90:H2",
    "TSC+H2in",
    "TSC+CC90+H2in",
    "TSC+H2in:CH4",

    "ESC",

    "Existing Capacities",
    "MS+MTO",

    "MS+MTO+CC90",
    "Dehydration NGfuel",
    "Dehydration H2fuel",
]

category_colors = {
    "TSC":                  "#e8630a",
    "Ret-TSC":              "#e8630a",   # same as TSC

    "TSC+CC90":             "#7a2e0e",
    "Ret-TSC+CC90":         "#7a2e0e",   # same as TSC+CC90

    "TSC:H2":               "#f5c518",
    "Ret-TSC:H2":           "#f5c518",   # same as TSC:H2
    "Existing TSC:H2":      "#f5c518",   # same as TSC:H2

    "MS+MTO":               "#9b59b6",
    "MS+MTO+CC90":          "#4a1a6e",

    "TSC+CC90:H2":          "#a07c00",
    "Ret-TSC+CC90:H2":      "#a07c00",   # same as TSC+CC90:H2

    "TSC+H2in":             "#3a8fd1",
    "Ret-TSC+H2in":         "#3a8fd1",   # same as TSC+H2in

    "TSC+H2in:CH4":         "#1a4f80",
    "Ret-TSC+H2in:CH4":     "#1a4f80",   # same as TSC+H2in:CH4

    "TSC+CC90+H2in":        "midnightblue",
    "Ret-TSC+CC90+H2in":    "midnightblue",   # same as TSC+CC90+H2in

    "Existing Capacities":  "#f5c518",   # same as TSC:H2 (existing thermal crackers)
    "ESC":                  "#808080",
    "Ret-ESC":              "#808080",   # same as ESC

    "Dehydration NGfuel":   "#57c46a",
    "Dehydration H2fuel":   "#1a6e30",
}

# Pattern encodes build type: "" = new build, "//" = retrofit (Ret-), ".." = existing
category_hatch = {
    "TSC":                  "",
    "Ret-TSC":              "//",
    "TSC+CC90":             "",
    "Ret-TSC+CC90":         "//",
    "TSC:H2":               "",
    "Ret-TSC:H2":           "//",
    "Existing TSC:H2":      "..",
    "MS+MTO":               "",
    "MS+MTO+CC90":          "",
    "TSC+CC90:H2":          "",
    "Ret-TSC+CC90:H2":      "//",
    "TSC+H2in":             "",
    "Ret-TSC+H2in":         "//",
    "TSC+H2in:CH4":         "",
    "Ret-TSC+H2in:CH4":     "//",
    "TSC+CC90+H2in":        "",
    "Ret-TSC+CC90+H2in":    "//",
    "Existing Capacities":  "..",
    "ESC":                  "",
    "Ret-ESC":              "//",
    "Dehydration NGfuel":   "",
    "Dehydration H2fuel":   "",
}

label_map = {
    "TSC":                  "TSC",
    "Ret-TSC":              "Ret-TSC",

    "TSC+CC90":             "TSC+CC90",
    "Ret-TSC+CC90":         "Ret-TSC+CC90",

    "TSC:H2":               "TSC:H2",
    "Ret-TSC:H2":           "Ret-TSC:H2",
    "Existing TSC:H2":      "Existing TSC:H2",

    "MS+MTO":               "MS+MTO",
    "MS+MTO+CC90":          "MS+MTO+CC90",

    "TSC+CC90:H2":          "TSC+CC90:H2",
    "Ret-TSC+CC90:H2":      "Ret-TSC+CC90:H2",

    "TSC+H2in":             "TSC+H2in",
    "Ret-TSC+H2in":         "Ret-TSC+H2in",

    "TSC+CC90+H2in":        "TSC+CC90+H2in",
    "Ret-TSC+CC90+H2in":    "Ret-TSC+CC90+H2in",

    "TSC+H2in:CH4":         "TSC+H2in:CH4",
    "Ret-TSC+H2in:CH4":     "Ret-TSC+H2in:CH4",

    "Existing Capacities":  "Existing Capacities",

    "Dehydration NGfuel":   "Dehydration NGfuel",
    "Dehydration H2fuel":   "Dehydration H2fuel",

    "ESC":                  "ESC",
    "Ret-ESC":              "Ret-ESC",
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

    Production edges are named like:
        CA_F-NGin_ethylene_production_edge
        Existing_CA_F-NGin-H2out_ethylene_production_edge
        CA_F-NGin_RETROFIT_ethylene_production_edge

    System-wide edges (e.g. Global_Ethylene_Use_*, the global demand row)
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
# Read MACRO ethylene balance for every scenario, tag rows with Zone
# ---------------------------------------------------------------------

zone_tables_by_scenario = {}
unzoned_production_by_scenario = {}

for scen_short, scen_path in macro_scenario_paths.items():
    macro_eth_path = os.path.join(
        macro_base_dir,
        scen_path,
        "annual_flow_results",
        "balance_specific_flows",
        "annual_flows_balance_Ethylene.csv",
    )

    if not os.path.exists(macro_eth_path):
        print(f"Warning: MACRO ethylene balance file not found: {macro_eth_path}")
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
    )

    macro_eth["Plot_Category"] = macro_eth["Category"]
    macro_eth["Zone"] = macro_eth["Edge"].apply(extract_zone)

    # Keep only rows that belong to a specific zone. This naturally drops
    # the global, non-zonal rows (Ethylene Demand, Global_Ethylene_Use_*),
    # since ethylene demand in this dataset is a single global node with
    # no per-zone breakdown.
    macro_eth_zoned = macro_eth[
        macro_eth["Zone"].notna() & macro_eth["Plot_Category"].notna()
    ].copy()

    # Production-category rows that didn't get a zone assigned would be
    # silently dropped from the by-zone tables above; track their total
    # so the production check below can flag any coverage gap.
    unzoned_production = macro_eth[
        macro_eth["Zone"].isna() &
        macro_eth["Plot_Category"].isin(desired_order)
    ]
    unzoned_production_by_scenario[scen_short] = unzoned_production["Annual_Flow"].sum()

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

    zone_table = zone_table[desired_order]

    zone_tables_by_scenario[scen_short] = zone_table

    print(f"\nEthylene production by zone — Scenario {scen_short} (tonnes):")
    print(zone_table)


# ---------------------------------------------------------------------
# Plot: one panel per scenario, zones as the stacked horizontal bars
# ---------------------------------------------------------------------

plotted_scenarios = [s for s in scenario_names if s in zone_tables_by_scenario]

# Union of categories that are actually non-trivial in at least one scenario,
# preserving desired_order, so the legend/colors stay consistent across panels.
active_cols = [
    col for col in desired_order
    if any(
        zone_tables_by_scenario[s][col].abs().sum() > 1.0
        for s in plotted_scenarios
    )
]

fig, axes = plt.subplots(
    len(plotted_scenarios), 1,
    figsize=(6.5, 2.6 * len(plotted_scenarios)),
    sharex=True,
)
if len(plotted_scenarios) == 1:
    axes = [axes]

for ax, scen in zip(axes, plotted_scenarios):
    plot_df = zone_tables_by_scenario[scen][active_cols]

    plot_df.plot(
        kind="barh",
        stacked=True,
        width=0.72,
        ax=ax,
        legend=False,
        color=[category_colors[col] for col in active_cols],
    )

    for container, col in zip(ax.containers, active_cols):
        hatch = category_hatch.get(col, "")
        for patch in container.patches:
            patch.set_hatch(hatch)
            patch.set_edgecolor("white" if hatch else "none")

    ax.set_yticklabels(zone_list, fontsize=11)
    ax.set_ylabel("")
    ax.set_title(f"Scenario {scen}", fontsize=12, loc="left")
    ax.tick_params(axis="x", labelsize=11)
    ax.axvline(x=0, color="black", linewidth=1, linestyle="--")
    ax.invert_yaxis()

axes[-1].set_xlabel("tonnes", fontsize=12)
fig.suptitle("Ethylene Production by Zone (tonnes)", fontsize=15)

handles, labels = axes[0].get_legend_handles_labels()
label_to_handle = dict(zip(labels, handles))
custom_handles = [label_to_handle[col] for col in active_cols if col in label_to_handle]
custom_labels = [label_map[col] for col in active_cols if col in label_to_handle]

fig.legend(
    custom_handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.02),
    ncol=3,
    fontsize=10,
    frameon=False,
)

plt.subplots_adjust(left=0.16, right=0.97, top=0.90, bottom=0.18, hspace=0.45)
plt.show()

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
                hovertemplate="%{fullData.name}: %{x:.2f} tonnes<extra></extra>",
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
    title="Ethylene Production by Zone (tonnes)",
    legend=dict(orientation="v", x=1.02, y=1, xanchor="left"),
    height=max(400, 280 * len(plotted_scenarios)),
)
fig_plotly.update_xaxes(title_text="tonnes", row=len(plotted_scenarios), col=1)

html_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "ethylene_byzone_macro_interactive.html",
)
fig_plotly.write_html(html_path)
webbrowser.open(f"file://{html_path}")

# ---------------------------------------------------------------------------
# Production check: total production summed across all zones/categories,
# flagging any production-category rows that didn't get a zone assigned
# (which would otherwise be silently missing from the plots above).
# ---------------------------------------------------------------------------
print("\nEthylene production check (sum across all zones and categories):")
for scen in plotted_scenarios:
    zoned_total = zone_tables_by_scenario[scen].to_numpy().sum()
    unzoned_total = unzoned_production_by_scenario.get(scen, 0.0)
    status = "OK" if abs(unzoned_total) < 1.0 else "WARNING: unzoned production found"
    print(
        f"  Scenario {scen}: Total production = {zoned_total:,.4f} tonnes  "
        f"[{status}]"
    )
    if abs(unzoned_total) >= 1.0:
        print(f"    -> {unzoned_total:,.4f} tonnes of production could not be assigned to a zone")
