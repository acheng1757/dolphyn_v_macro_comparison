import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import sys

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)

plt.rcParams["font.family"] = "Arial"

# ---------------------------------------------------------------------
# Paths and scenarios
# ---------------------------------------------------------------------

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir, macro_results_folder,
    dolphyn_results_folder, scenario_names,
)

dolphyn_scenario_paths = {
    scenario_names[0]: f"all_demand_test/{dolphyn_results_folder}",
}

macro_scenario_paths = {
    scenario_names[0]: f"clean_slate_5_25/results_1848h_all/results",
    scenario_names[1]: f"try_again_5_31_1848/results_001/results",
}

_scen_folder = dolphyn_scenario_paths[scenario_names[0]]

bf_results_files = [
    os.path.join(dolphyn_base_dir, _scen_folder, "Results_BESC/BESC_Bio_LF_capacity.csv"),
]

sf_results_files = [
    os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/Synfuel_capacity.csv"),
]

fuels_balance_files = {
    "Gasoline": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Gasoline_balance.csv"),
    ],
    "Jetfuel": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Jetfuel_balance.csv"),
    ],
    "Diesel": [
        os.path.join(dolphyn_base_dir, _scen_folder, "Results_LF/LF_Diesel_balance.csv"),
    ],
}

conversion_factor = 0.293071 * 3.6e-9
macro_conversion_factor = 3.6e-9

FOSSIL_COL = {
    'Gasoline': 'Conventional_Gasoline',
    'Jetfuel':  'Conventional_Jetfuel',
    'Diesel':   'Conventional_Diesel',
}
DEMAND_COL = {
    'Gasoline': 'Gasoline_Demand',
    'Jetfuel':  'Jetfuel_Demand',
    'Diesel':   'Diesel_Demand',
}
BIO_COL = {
    'Gasoline': 'Bio_Gasoline',
    'Jetfuel':  'Bio_Jetfuel',
    'Diesel':   'Bio_Diesel',
}
SYN_COL = {
    'Gasoline': 'Syn_Gasoline',
    'Jetfuel':  'Syn_Jetfuel',
    'Diesel':   'Syn_Diesel',
}


# ---------------------------------------------------------------------
# Dolphyn liquid-fuel balance
# ---------------------------------------------------------------------

def load_bf_results(files, scenario_names):
    dfs = []
    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df["Scenario"] = scenario
        df["Total_Biofuel_Production"] = (
            df["Annual_Biogasoline_Production"] +
            df["Annual_Biojetfuel_Production"] +
            df["Annual_Biodiesel_Production"]
        ) * conversion_factor
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def categorize_bf_resource(resource):
    if resource == 'Total':
        return None
    elif 'Gasoline_Gasification_CCS_99' in resource:
        return 'Bio MeOH - Gasoline High CCS'
    elif 'Gasoline_Gasification_CCS_31' in resource:
        return 'Bio MeOH - Gasoline Low CCS'
    elif 'Gasoline_Gasification' in resource and 'CCS' not in resource:
        return 'Bio MeOH - Gasoline Non CCS'
    elif 'Pyrolysis_CCS_99' in resource:
        return 'Pyrolysis High CCS'
    elif 'Pyrolysis' in resource and 'CCS' not in resource:
        return 'Pyrolysis Non CCS'
    elif 'FT_High_Diesel_CCS_99' in resource:
        return 'Bio FT (High Diesel) High CCS'
    elif 'FT_High_Diesel_CCS_53' in resource:
        return 'Bio FT (High Diesel) Low CCS'
    elif 'FT_High_Diesel' in resource and 'CCS' not in resource:
        return 'Bio FT (High Diesel) Non CCS'
    elif 'FT_High_Jetfuel_CCS_84' in resource:
        return 'Bio FT (High Jetfuel) CCS 84'
    elif 'FT_High_Jetfuel_CCS_75' in resource:
        return 'Bio FT (High Jetfuel) CCS 75'
    elif 'FT_High_Jetfuel_CCS_99' in resource:
        return 'Bio FT (High Jetfuel) CCS 99'
    else:
        return None


def load_sf_results(files, scenario_names):
    dfs = []
    for file, scenario in zip(files, scenario_names):
        df = pd.read_csv(file)
        df["Scenario"] = scenario
        df["Total_Synfuel_Production"] = (
            df["Annual_Syngasoline_Production"] +
            df["Annual_Synjetfuel_Production"] +
            df["Annual_Syndiesel_Production"]
        ) * conversion_factor
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def categorize_sf_resource(resource):
    if "Synfuel_Plant" in resource and "CCS" not in resource:
        return "SFT Non CCS"
    elif "Synfuel_Plant_wCCS" in resource:
        return "SFT CCS"


def read_global_annualsum(file, target_col):
    """Return the AnnualSum value for the Global zone of target_col."""
    df_raw = pd.read_csv(file, header=None)
    col_names = df_raw.iloc[0]
    zone_ids  = df_raw.iloc[1]
    mask = df_raw.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)
    if not mask.any():
        return 0.0
    annual_row = df_raw[mask].iloc[0]
    for i in range(1, len(col_names)):
        if (str(col_names.iloc[i]).strip() == target_col and
                str(zone_ids.iloc[i]).strip() == 'Global'):
            return pd.to_numeric(annual_row.iloc[i], errors='coerce') * conversion_factor
    return 0.0


def load_fossil_fuel_balances(files, scenario_names):
    dfs = []
    for fuel_type, file_list in files.items():
        fossil_col = FOSSIL_COL[fuel_type]
        demand_col = DEMAND_COL[fuel_type]
        for file, scenario in zip(file_list, scenario_names):
            df = pd.read_csv(file)
            annual_row = df[df.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)]
            fossil_value = pd.to_numeric(annual_row[fossil_col].values[0], errors='coerce') * conversion_factor
            demand_value = pd.to_numeric(annual_row[demand_col].values[0], errors='coerce') * conversion_factor
            dfs.append(pd.DataFrame({
                'Scenario': [scenario],
                'Fossil':   [fossil_value],
                'Demand':   [demand_value],
            }))
    return pd.concat(dfs, ignore_index=True)


# Load biofuel results and categorize
bf_data = load_bf_results(bf_results_files, scenario_names)
bf_data["Resource_Category"] = bf_data["Resource"].apply(categorize_bf_resource)

bf_aggregated = (
    bf_data
    .groupby(["Scenario", "Resource_Category"])["Total_Biofuel_Production"]
    .sum()
    .unstack()
    .fillna(0)
)

# Load synfuel results and categorize
sf_data = load_sf_results(sf_results_files, scenario_names)
sf_data["Resource_Category"] = sf_data["Resource"].apply(categorize_sf_resource)

sf_aggregated = (
    sf_data
    .groupby(["Scenario", "Resource_Category"])["Total_Synfuel_Production"]
    .sum()
    .unstack()
    .fillna(0)
)

# Load fossil and demand results
fossil_data = load_fossil_fuel_balances(fuels_balance_files, scenario_names)
fossil_aggregated = fossil_data.groupby('Scenario')[['Fossil']].sum()
demand_aggregated = fossil_data.groupby('Scenario')[['Demand']].sum()

# Compute AnnualSum row totals per fuel type for balance check
annualsum_row_totals = {}
for fuel_type, file_list in fuels_balance_files.items():
    for file, scenario in zip(file_list, scenario_names):
        df = pd.read_csv(file)
        annual_row = df[df.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)]
        if not annual_row.empty:
            numeric_vals = annual_row.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
            total = numeric_vals.sum(axis=1).values[0] * conversion_factor
        else:
            total = 0.0
        annualsum_row_totals.setdefault(scenario, {})[fuel_type] = total

# Read Bio and Syn totals from balance file Global columns for cross-referencing
bio_balance_totals = {s: 0.0 for s in scenario_names}
syn_balance_totals = {s: 0.0 for s in scenario_names}
for fuel_type, file_list in fuels_balance_files.items():
    for file, scenario in zip(file_list, scenario_names):
        bio_balance_totals[scenario] += read_global_annualsum(file, BIO_COL[fuel_type])
        syn_balance_totals[scenario] += read_global_annualsum(file, SYN_COL[fuel_type])

# Combine all Dolphyn data
dolphyn_combined_data = bf_aggregated.join(fossil_aggregated, on="Scenario", how="left").fillna(0)
dolphyn_combined_data = sf_aggregated.join(dolphyn_combined_data, on="Scenario", how="left").fillna(0)
dolphyn_combined_data = dolphyn_combined_data.join(demand_aggregated, on="Scenario", how="left").fillna(0)
dolphyn_combined_data = dolphyn_combined_data.reindex(scenario_names).fillna(0)

# Cross-reference: add residual production not captured by capacity-file categories
for scenario in scenario_names:
    bio_from_capacity = bf_aggregated.loc[scenario].sum() if scenario in bf_aggregated.index else 0.0
    missing_bio = bio_balance_totals.get(scenario, 0.0) - bio_from_capacity
    if abs(missing_bio) > 1e-6:
        dolphyn_combined_data.loc[scenario, 'Other Bio LF'] = missing_bio

    syn_from_capacity = sf_aggregated.loc[scenario].sum() if scenario in sf_aggregated.index else 0.0
    missing_syn = syn_balance_totals.get(scenario, 0.0) - syn_from_capacity
    if abs(missing_syn) > 1e-6:
        dolphyn_combined_data.loc[scenario, 'Other Syn LF'] = missing_syn

dolphyn_combined_data = dolphyn_combined_data.fillna(0)


# ---------------------------------------------------------------------
# Desired order, colors, and labels (matching LF_Dolphyn.py)
# ---------------------------------------------------------------------

desired_order = [
    'Demand',
    'Bio MeOH - Gasoline Non CCS',
    'Bio MeOH - Gasoline Low CCS',
    'Bio MeOH - Gasoline High CCS',
    'Pyrolysis Non CCS',
    'Pyrolysis High CCS',
    'Bio FT (High Diesel) Non CCS',
    'Bio FT (High Diesel) Low CCS',
    'Bio FT (High Diesel) High CCS',
    'Bio FT (High Jetfuel) CCS 75',
    'Bio FT (High Jetfuel) CCS 84',
    'Bio FT (High Jetfuel) CCS 99',
    'Other Bio LF',
    'SFT Non CCS',
    'SFT CCS',
    'Other Syn LF',
    'Fossil',
]

dolphyn_combined_data = dolphyn_combined_data[
    [col for col in desired_order if col in dolphyn_combined_data.columns]
]

category_colors = {
    'Demand':                        'bisque',
    'Bio MeOH - Gasoline Non CCS':  'lightblue',
    'Bio MeOH - Gasoline High CCS': 'royalblue',
    'Bio MeOH - Gasoline Low CCS': 'cornflowerblue',
    'Pyrolysis Non CCS':            'peachpuff',
    'Pyrolysis High CCS':           'darkorange',
    'Bio FT (High Diesel) Non CCS': 'limegreen',
    'Bio FT (High Diesel) High CCS': 'forestgreen',
    'Bio FT (High Diesel) Low CCS': 'forestgreen',
    'Bio FT (High Jetfuel) CCS 84': 'sandybrown',
    'Bio FT (High Jetfuel) CCS 75': 'sandybrown',
    'Bio FT (High Jetfuel) CCS 99': 'chocolate',
    'Other Bio LF':                 'darkseagreen',
    'SFT Non CCS':                  'purple',
    'SFT CCS':                      'indigo',
    'Other Syn LF':                 'mediumpurple',
    'Fossil':                       'grey',
}

label_map = {
    'Demand':                        'Demand',
    'Bio MeOH - Gasoline Non CCS':  'Bio-MTG',
    'Bio MeOH - Gasoline High CCS': 'Bio-MTG CC99',
    'Bio MeOH - Gasoline Low CCS': 'Bio-MTG CC31',
    'Pyrolysis Non CCS':            'Pyrolysis',
    'Pyrolysis High CCS':           'Pyrolysis CC99',
    'Bio FT (High Diesel) Non CCS': 'Bio-FT (Diesel)',
    'Bio FT (High Diesel) High CCS': 'Bio-FT (Diesel) CC99',
    'Bio FT (High Diesel) Low CCS': 'Bio-FT (Diesel) CC53',
    'Bio FT (High Jetfuel) CCS 84': 'Bio-FT (Jet) CC84',
    'Bio FT (High Jetfuel) CCS 75': 'Bio-FT (Jet) CC75',
    'Bio FT (High Jetfuel) CCS 99': 'Bio-FT (Jet) CC99',
    'Other Bio LF':                 'Other Bio LF',
    'SFT Non CCS':                  'Syn-FT',
    'SFT CCS':                      'Syn-FT CC99',
    'Other Syn LF':                 'Other Syn LF',
    'Fossil':                       'Fossil Liquids',
}


# ---------------------------------------------------------------------
# MACRO liquid-fuel balance
# ---------------------------------------------------------------------

def find_macro_lf_balance_file(results_dir):
    """Try likely liquid-fuels balance file names."""
    balance_dir = os.path.join(results_dir, "annual_flow_results", "balance_specific_flows")

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
    """Map MACRO LF balance rows to the same plotting categories as Dolphyn."""
    sector = str(row.get("Sector", "")).strip()
    category = str(row.get("Category", "")).strip()
    edge = str(row.get("Edge", "")).strip()

    sector_lower = sector.lower()
    category_lower = category.lower()
    edge_lower = edge.lower()

    text = f"{sector_lower} {category_lower} {edge_lower}"

    if sector == "Demand" or "demand" in text:
        return None

    # Synthetic liquid fuels
    if sector == "Synthetic fuels" or "synthetic" in sector_lower:
        if "wccs" in text or "ccs" in text or "cc99" in text:
            return "SFT CCS"
        if "s-j" in text or "synfuel" in text or "synthetic" in text or "ft" in text:
            return "SFT Non CCS"
        return None

    # Bioenergy liquid fuels
    if sector == "Bioenergy" or "bio" in sector_lower:
        if "gasification_ccs_99" in text or ("gasification" in text and "99" in text):
            return "Bio MeOH - Gasoline High CCS"
        if "gasification_ccs_31" in text or ("gasification" in text and "31" in text):
            return "Bio MeOH - Gasoline Low CCS"
        if "gasification_non_ccs" in text or ("gasification" in text and "non" in text):
            return "Bio MeOH - Gasoline Non CCS"
        if "pyrolysis_ccs_99" in text or ("pyrolysis" in text and "99" in text):
            return "Pyrolysis High CCS"
        if "pyrolysis" in text and "ccs" not in text:
            return "Pyrolysis Non CCS"
        if "high_diesel_ccs_53" in text or ("high_diesel" in text and "53" in text):
            return "Bio FT (High Diesel) Low CCS"
        if "high_diesel_ccs_99" in text or ("high_diesel" in text and "99" in text):
            return "Bio FT (High Diesel) High CCS"
        if "high_diesel_non_ccs" in text or ("high_diesel" in text and "non" in text):
            return "Bio FT (High Diesel) Non CCS"
        if "ft_high_jetfuel_ccs_84" in text or ("high_jetfuel" in text and "84" in text):
            return "Bio FT (High Jetfuel) CCS 84"
        if "ft_high_jetfuel_ccs_75" in text or ("high_jetfuel" in text and "75" in text):
            return "Bio FT (High Jetfuel) CCS 75"
        if "high_jetfuel" in text:
            return "Bio FT (High Jetfuel) CCS 99"
        return None

    # Exclude primary-energy input edges (raw resource side); keep fuel output edges only
    if "fossil_fuel_edge" in edge_lower:
        return None

    # Fossil liquid fuels
    if "fossil" in text or "petroleum" in text or "refinery" in text or "oil" in text:
        return "Fossil"

    return None


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

    macro_lf["Plot_Category"] = macro_lf.apply(map_macro_lf_category, axis=1)
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
# Align Dolphyn and MACRO columns for paired plot
# ---------------------------------------------------------------------

all_data_cols = set(dolphyn_combined_data.columns) | set(macro_combined_data.columns)
full_desired_order = [col for col in desired_order if col in all_data_cols]

for col in full_desired_order:
    if col not in macro_combined_data.columns:
        macro_combined_data[col] = 0.0
    if col not in dolphyn_combined_data.columns:
        dolphyn_combined_data[col] = 0.0

macro_combined_data = (
    macro_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [full_desired_order]
)

dolphyn_combined_data = (
    dolphyn_combined_data
    .reindex(scenario_names)
    .fillna(0.0)
    [full_desired_order]
)

print("\nDolphyn liquid fuels balance by scenario (EJ):")
print(dolphyn_combined_data)

print("\nMACRO liquid fuels production by scenario (EJ):")
print(macro_combined_data)


# ---------------------------------------------------------------------
# Build paired plotting table
# ---------------------------------------------------------------------

plot_rows = []
plot_index = []

for scen in scenario_names:
    plot_rows.append(dolphyn_combined_data.loc[scen, full_desired_order])
    plot_index.append((scen, "Dolphyn"))

    plot_rows.append(macro_combined_data.loc[scen, full_desired_order])
    plot_index.append((scen, "MACRO"))

plot_df = pd.DataFrame(plot_rows)
plot_df.index = pd.MultiIndex.from_tuples(
    plot_index,
    names=["Scenario", "Model"],
)

y_tick_labels = [
    "D" if model == "Dolphyn" else "M"
    for _, model in plot_df.index
]


# ---------------------------------------------------------------------
# Plot Dolphyn and MACRO side by side
# ---------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(5.2, 4.4))

pair_gap = 0.45
bar_height = 0.72

bar_positions = []

for i in range(len(scenario_names)):
    base = i * (2 + pair_gap)
    bar_positions.extend([base, base + 1])

plot_df.plot(
    kind="barh",
    stacked=True,
    width=bar_height,
    ax=ax,
    color=[category_colors.get(col, "#333333") for col in full_desired_order],
)

for container in ax.containers:
    for patch, y in zip(container.patches, bar_positions):
        patch.set_y(y - bar_height / 2)
        patch.set_height(bar_height)

ax.set_yticks(bar_positions)
ax.set_yticklabels(y_tick_labels, fontsize=14)

ax.set_ylabel("")
ax.set_title("Total LF Balance (EJ)", fontsize=16)
ax.tick_params(axis="x", labelsize=14)

ax.set_xlim(0, 13)
ax.set_xticks([0, 4, 8, 12])
ax.axvline(x=0, color="black", linewidth=1, linestyle="--")

for i, scen in enumerate(scenario_names):
    y_mid = i * (2 + pair_gap) + 0.5
    ax.text(
        -0.16,
        y_mid,
        scen,
        transform=ax.get_yaxis_transform(),
        ha="right",
        va="center",
        fontsize=14,
    )

ax.set_ylim(max(bar_positions) + 0.8, -0.8)

handles, _ = ax.get_legend_handles_labels()
custom_labels = [label_map[col] for col in full_desired_order]

ax.legend(
    handles,
    custom_labels,
    loc="upper center",
    bbox_to_anchor=(0.5, -0.28),
    ncol=2,
    fontsize=11,
    frameon=False,
)

plt.subplots_adjust(left=0.24, right=0.98, top=0.88, bottom=0.40)

plt.show()

# Print balance summary
print()
for scenario in scenario_names:
    print(f'Scenario: {scenario}')

    d_row = dolphyn_combined_data.loc[scenario]
    d_pos = d_row[d_row > 0].sum()
    d_neg = d_row[d_row < 0].sum()
    d_net = d_row.sum()
    totals = annualsum_row_totals.get(scenario, {})
    combined_total = sum(totals.values())
    for fuel_type in ('Gasoline', 'Jetfuel', 'Diesel'):
        print(f'  Dolphyn AnnualSum ({fuel_type:8s}) : {totals.get(fuel_type, float("nan")):+.4f} EJ')
    print(f'  Dolphyn AnnualSum (combined)   : {combined_total:+.4f} EJ')
    print(f'  Dolphyn plot net               : {d_net:+.4f} EJ  (pos: {d_pos:+.4f},  neg: {d_neg:+.4f})')

    m_row = macro_combined_data.loc[scenario]
    m_pos = m_row[m_row > 0].sum()
    m_neg = m_row[m_row < 0].sum()
    m_net = m_row.sum()
    print(f'  MACRO   plot net               : {m_net:+.4f} EJ  (pos: {m_pos:+.4f},  neg: {m_neg:+.4f})')
    print()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------
y_plotly_labels = [
    f"{scen} ({'D' if model == 'Dolphyn' else 'M'})"
    for scen, model in plot_df.index
]

fig_plotly = go.Figure()

for col in full_desired_order:
    display_name = label_map.get(col, col)
    color = category_colors.get(col, '#333333')
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=y_plotly_labels,
        x=plot_df[col].tolist(),
        orientation='h',
        marker_color=color,
        hovertemplate='%{fullData.name}: %{x:.4f} EJ<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Total LF Balance (EJ)',
    xaxis_title='EJ',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(plot_df) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(400, 80 * len(plot_df)),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lf_d_vs_m_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')
