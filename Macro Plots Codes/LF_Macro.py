import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------

# flows.csv already has signs for consumption and production
# (-) means consumption pointing towards the asset
# (+) means production pointing away from the asset

# If there is both consumption AND production, then it will show as a net total in the plot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_scenario_paths, load_annual_nsd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

# MACRO annual_flow values are treated as MWh.
macro_conversion_factor = 3.6e-9

# ---------------------------------------------------------------------
# Desired order, colors, and labels
# ---------------------------------------------------------------------

desired_order = [
    "Demand",
    "Gasoline Blending",
    "Non-Served Demand",
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
    "Ethanol to Gasoline Diesel",
    "Fossil",
]

category_colors = {
    "Demand": "bisque",
    "Gasoline Blending": "steelblue",
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
    "Ethanol to Gasoline Diesel": "#ffd700",
    "Fossil": "grey",
    "Non-Served Demand": "red",
}

label_map = {
    "Demand": "Demand",
    "Gasoline Blending": "Gasoline Blending",
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
    "Ethanol to Gasoline Diesel": "Eth. Upgrading (Gasoline+Diesel)",
    "Fossil": "Fossil Liquids",
    "Non-Served Demand": "Non-Served Demand",
}


# ---------------------------------------------------------------------
# MACRO liquid-fuel balance helpers
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

    # Demand rows
    if sector == "Demand" or "demand" in text:
        # Gasoline_MW_Global is now the post-blending demand node — the
        # pre-blending gasoline requirement is captured separately by the
        # "Gasoline Blending" category below, sourced from the blending
        # asset's gasoline_edge. Counting both here would double count.
        if edge == "Gasoline_MW_Global":
            return None
        return "Demand"

    # Synthetic liquid fuels
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

    # Bioenergy liquid fuels
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

    # Exclude the upstream resource-consumption edge of the newer
    # FossilFuelsUpstream asset structure. Each fuel's "*_fuel_edge" (the
    # actual liquid-fuel supply, positive) is mirrored by a "*_fossil_fuel_edge"
    # (the upstream resource it consumes, negative) — both share Category
    # "Fossil Liquid Fuels", so excluding by edge suffix (rather than by
    # category) is what lets the real supply edge fall through to the
    # match below. The older ConstrainedFossilLiquidFuels asset has no
    # such edge, so this never affects that structure.
    if "fossil_fuel_edge" in edge_lower:
        return None

    # Fossil liquid fuels — covers both the older "Fossil Petroleum
    # Refinery" category and the newer "Fossil Liquid Fuels" /
    # "*_Fossil_Upstream_*" naming.
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
# Read MACRO liquid-fuel balance
# ---------------------------------------------------------------------

macro_lf_tables = []

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

    macro_lf["Scenario"] = scen_short

    macro_lf["Annual_Flow"] = (
        pd.to_numeric(macro_lf["Annual_Flow"], errors="coerce")
        .fillna(0.0)
        * macro_conversion_factor
    )

    macro_lf["Plot_Category"] = macro_lf.apply(
        map_macro_lf_category,
        axis=1,
    )

    # Exclude demand and unmapped rows
    macro_lf = macro_lf[macro_lf["Plot_Category"].notna()].copy()

    macro_lf_tables.append(macro_lf)


if macro_lf_tables:
    macro_lf_combined = pd.concat(macro_lf_tables, ignore_index=True)

    macro_combined_data = (
        macro_lf_combined
        .groupby(["Scenario", "Plot_Category"])["Annual_Flow"]
        .sum()
        .unstack()
        .fillna(0.0)
        .reindex(scenario_names)
        .fillna(0.0)
    )
else:
    macro_combined_data = pd.DataFrame(index=scenario_names)


# ---------------------------------------------------------------------
# Add Ethanol_to_X LF production split by process
# ---------------------------------------------------------------------
# Ethanol_to_X assets are tagged as "Ethanol Upgrading" in Step 1, so they
# are absent from the Liquid_Fuels balance file.  We pull their LF
# output edges from the all_nonzero file, one category per process.
# Diesel_JetFuel must be matched before plain Diesel to avoid overlap.

_LF_PROD_EDGES = (
    "gasoline_production_edge",
    "diesel_production_edge",
    "jetfuel_production_edge",
)

# (plot_category, asset_substring, exclude_substring_or_None)
_ETHANOL_UPGRADING_ASSETS = [
    ("Ethanol to Gasoline",      "_Ethanol_to_Gasoline_",      "_Ethanol_to_Gasoline_Diesel_"),
    ("Ethanol to Gasoline Diesel", "_Ethanol_to_Gasoline_Diesel_", None),
    ("Ethanol to Diesel",        "_Ethanol_to_Diesel_",       None),
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


for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    process_flows = _load_ethanol_upgrading_by_process(results_dir)
    for cat, raw_flow in process_flows.items():
        if cat not in macro_combined_data.columns:
            macro_combined_data[cat] = 0.0
        if scen_short in macro_combined_data.index:
            macro_combined_data.loc[scen_short, cat] = raw_flow * macro_conversion_factor


# ---------------------------------------------------------------------
# Add Gasoline Blending demand (gasoline inflow into the blending asset)
# ---------------------------------------------------------------------
# Gasoline_MW_Global (excluded from "Demand" above) is now the post-blend
# demand node. The actual requirement LF/gasoline producers must supply is
# the flow into Global_Gasoline_Blending's gasoline_edge — the inflow, not
# the gasoline_blend_edge outflow. This edge isn't classified by Step 1
# (Sector/Category = NA), so we pull it directly from the all_nonzero file.

def _load_gasoline_blending_gasoline_demand(results_dir):
    """Return the annual gasoline inflow (MWh) into Global_Gasoline_Blending's gasoline_edge."""
    path = os.path.join(
        results_dir,
        "annual_flow_results",
        "all_nonzero_annual_flows_with_categories.csv",
    )
    if not os.path.exists(path):
        return 0.0
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    if "Edge" not in df.columns or "Annual_Flow" not in df.columns:
        return 0.0
    flows = pd.to_numeric(df["Annual_Flow"], errors="coerce").fillna(0.0)
    mask = df["Edge"] == "Global_Gasoline_Blending_gasoline_edge"
    return flows[mask].sum()


for scen_short, scen_path in macro_scenario_paths.items():
    results_dir = os.path.join(macro_base_dir, scen_path)
    blending_gasoline_flow = _load_gasoline_blending_gasoline_demand(results_dir)
    if "Gasoline Blending" not in macro_combined_data.columns:
        macro_combined_data["Gasoline Blending"] = 0.0
    if scen_short in macro_combined_data.index:
        macro_combined_data.loc[scen_short, "Gasoline Blending"] = blending_gasoline_flow * macro_conversion_factor


# ---------------------------------------------------------------------
# Align columns
# ---------------------------------------------------------------------

for col in desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0

for scen_short, scen_path in macro_scenario_paths.items():
    if scen_short in macro_combined_data.index:
        nsd = load_annual_nsd(scen_path, ["gasoline_", "diesel_", "jetfuel_"]) * macro_conversion_factor
        macro_combined_data.loc[scen_short, "Non-Served Demand"] = nsd

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [desired_order]
)

print("\nMACRO liquid fuels production by scenario (EJ), demand excluded:")
print(macro_combined_data)

# ---------------------------------------------------------------------
# Balance check: sum of positives vs negatives per scenario
# ---------------------------------------------------------------------
print("Liquid Fuels balance check:")
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
# Plot MACRO-only liquid-fuels production
# ---------------------------------------------------------------------

plot_df = macro_combined_data.copy()

fig, ax = plt.subplots(figsize=(5.2, 3.2))

plot_df.plot(
    kind="barh",
    stacked=True,
    width=0.72,
    ax=ax,
    color=[category_colors.get(col, "#333333") for col in desired_order],
)

ax.set_yticklabels(scenario_names, fontsize=14)

ax.set_ylabel("")
ax.set_title("Total LF Prod. (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

_pos_ext = plot_df.clip(lower=0).sum(axis=1).max()
_neg_ext = plot_df.clip(upper=0).sum(axis=1).min()
_pad = max(abs(_pos_ext), abs(_neg_ext)) * 0.12 or 1.0
ax.set_xlim(_neg_ext - _pad, _pos_ext + _pad)
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

# Keep HB-HS at the top
ax.invert_yaxis()

# Custom legend
handles, _ = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.30),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.20, right=0.98, top=0.86, bottom=0.40)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------

_active_cols = [col for col in desired_order if plot_df[col].abs().sum() > 0]

fig_plotly = go.Figure()
for col in _active_cols:
    fig_plotly.add_trace(go.Bar(
        name=label_map.get(col, col),
        y=scenario_names,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=category_colors.get(col, '#333333'),
        hovertemplate='%{fullData.name}: %{x:.4f} EJ<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Total LF Prod. (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lf_macro_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')