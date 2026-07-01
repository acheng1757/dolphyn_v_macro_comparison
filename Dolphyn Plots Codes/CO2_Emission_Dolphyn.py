import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import webbrowser
import os
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names


# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/ethylene_only_test/{dolphyn_results_folder}/Results_CSC/Zone_CO2_emission_balance.csv']

# Columns of interest for summation
columns_of_interest = ["Power Emissions", 
                       "H2 Emissions", 
                       "DAC Emissions", 
                       "Bio Elec Plant Emissions", 
                       "Biomass CO2 for Bio Elec", 
                       "Bio H2 Plant Emissions",
                       "Biomass CO2 for Bio H2", 
                       "Bio LF Plant Emissions", 
                       "Biomass CO2 for Bio LF", 
                       "Bio NG Plant Emissions", 
                       "Biomass CO2 for Bio NG", 
                       "Conventional NG", 
                       "Syn NG Plant Emissions", 
                       "Synthetic NG", 
                       "Bio NG", 
                       "Synfuel Plant Emissions", 
                       "Syn Gasoline", 
                       "Syn Jetfuel", 
                       "Syn Diesel", 
                       "Bio Gasoline",
                       "Bio Jetfuel",
                       "Bio Diesel",
                       "Conventional Gasoline",
                       "Conventional Jetfuel",
                       "Conventional Diesel",
                       "NG Reduction from Power CCS", 
                       "NG Reduction from H2 CCS", 
                       "NG Reduction from DAC CCS",
                       "Ethylene Production",
                       "Bio Ethanol Plant Emissions",
                       "Biomass CO2 for Bio Ethanol",
                       "Ethylene Combustion"
                       ]


# Conversion factor (example)
conversion_factor = 1e-6  # Adjust as needed

# Initialize a dictionary to store values for each scenario
global_values_per_scenario = {}
annualsum_row_totals = {}  # full AnnualSum row total across all columns and zones

# Process each file
for path, scenario in zip(file_paths, scenario_names):
    # Read without header so we can use the Zone row to pick Global columns
    df_raw = pd.read_csv(path, header=None)
    col_names = df_raw.iloc[0]   # row 0 = column names
    zone_ids  = df_raw.iloc[1]   # row 1 = zone identifiers

    # Find the AnnualSum row
    annualsum_mask = df_raw.iloc[:, 0].astype(str).str.contains('AnnualSum', case=False, na=False)

    if annualsum_mask.any():
        annualsum_row = df_raw[annualsum_mask].iloc[0]

        # Identify which column names only appear in Global (no zone-specific rows)
        non_global_col_names = set(
            col_names.iloc[i] for i in range(1, len(col_names))
            if str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')
        )

        # Full row total: zone-specific columns + any Global-only columns
        zone_indices = [i for i in range(1, len(col_names))
                        if str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')]
        global_only_indices = [i for i in range(1, len(col_names))
                               if str(zone_ids.iloc[i]).strip() == 'Global'
                               and col_names.iloc[i] not in non_global_col_names]
        annualsum_row_totals[scenario] = sum(
            float(annualsum_row.iloc[i]) for i in zone_indices + global_only_indices
            if str(annualsum_row.iloc[i]).strip() not in ('', 'nan')
        ) * conversion_factor

        extracted = {}
        for col_name in columns_of_interest:
            # Prefer zone-specific columns; fall back to Global for Global-only columns
            zone_matches = [i for i in range(len(col_names))
                            if col_names.iloc[i] == col_name
                            and str(zone_ids.iloc[i]).strip() not in ('Global', 'Zone', '')]
            if zone_matches:
                extracted[col_name] = sum(float(annualsum_row.iloc[i]) for i in zone_matches) * conversion_factor
            else:
                global_matches = [i for i in range(len(col_names))
                                  if col_names.iloc[i] == col_name
                                  and str(zone_ids.iloc[i]).strip() == 'Global']
                extracted[col_name] = sum(float(annualsum_row.iloc[i]) for i in global_matches) * conversion_factor if global_matches else 0.0
        extracted_values = pd.Series(extracted)
    else:
        extracted_values = pd.Series([0] * len(columns_of_interest), index=columns_of_interest)
        annualsum_row_totals[scenario] = 0.0

    # Store the values for this scenario
    global_values_per_scenario[scenario] = extracted_values

# Convert the dictionary to a DataFrame for plotting
combined_data = pd.DataFrame(global_values_per_scenario).T  # Transpose for easier plotting

combine_mapping = {
    'Power Emissions': 'Conventional NG',
    "NG Reduction from Power CCS": 'Conventional NG',
    
    'HSC Emissions': 'Conventional NG',
    'NG Reduction from H2 CCS': 'Conventional NG',
    
    'CSC Emissions': 'DAC Capture',
    'NG Reduction from DAC CCS': 'DAC Capture',
    
    'Biomass CO2 for Bio Elec': 'Biomass Capture',
    'Biomass CO2 for Bio H2': 'Biomass Capture',
    'Biomass CO2 for Bio LF': 'Biomass Capture',
    'Biomass CO2 for Bio NG': 'Biomass Capture',
    "Biomass CO2 for Bio Ethanol" : 'Biomass Capture',
    
    'Bio Elec Plant Emissions': 'Biofuels process',
    'Bio H2 Plant Emissions': 'Biofuels process',
    'Bio LF Plant Emissions': 'Biofuels process',
    'Bio NG Plant Emissions': 'Biofuels process',
    'Biofuels': 'Biofuels process',
    'Bio NG': 'Biofuels processes',
    "Bio Ethanol Plant Emissions": 'Biofuels processes',
    
    'Syn NG Plant Emissions': 'Synthetic NG and processes',
    'Syn NG': 'Synthetic NG and processes',
    
    'Synfuel Plant Emissions': 'Synthetic Fuels and processes',
    'Synfuels': 'Synthetic Fuels and processes',

    "Ethylene Production" : "Ethylene Production",
    "Ethylene Combustion" : "Ethylene End of Life"

}

# Custom order for arranging individual categories
desired_order = [
    # Biomass CO2 captures — greens
    'Biomass CO2 for Bio Elec',
    'Biomass CO2 for Bio H2',
    'Biomass CO2 for Bio LF',
    'Biomass CO2 for Bio NG',
    'Biomass CO2 for Bio Ethanol',
    # DAC
    'DAC Emissions',
    'NG Reduction from DAC CCS',
    # NG reductions from CCS
    'NG Reduction from Power CCS',
    'NG Reduction from H2 CCS',
    # Fossil fuels — reds/greys
    'Conventional NG',
    'Conventional Gasoline',
    'Conventional Jetfuel',
    'Conventional Diesel',
    # Power & H2
    'Power Emissions',
    'H2 Emissions',
    # Bio process emissions — amber
    'Bio Elec Plant Emissions',
    'Bio H2 Plant Emissions',
    'Bio LF Plant Emissions',
    'Bio NG Plant Emissions',
    'Bio Ethanol Plant Emissions',
    'Bio NG',
    # Bio liquid fuel emissions — cyan/teal
    'Bio Gasoline',
    'Bio Jetfuel',
    'Bio Diesel',
    # Synthetic fuels — purple/indigo
    'Syn NG Plant Emissions',
    'Synthetic NG',
    'Synfuel Plant Emissions',
    'Syn Gasoline',
    'Syn Jetfuel',
    'Syn Diesel',
    # Ethylene — pink
    'Ethylene Production',
    'Ethylene Combustion',
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

# Custom colors and display names
# Color families:
#   Biomass CO2 captures (non-ethanol) → greens
#   Bio Ethanol (capture + plant emissions) → yellows
#   Other bio plant emissions            → orange/amber
#   All NG-related                       → reds  (dark=fossil, lighter=CCS reductions)
#   Power Emissions                      → deep orange
#   H2 Emissions                         → blue
#   DAC Emissions                        → navy
#   Synthetic fuels                      → purples
#   Ethylene                             → pink/magenta
category_colors = {
    # Biomass CO2 captures (non-ethanol) — green family
    'Biomass CO2 for Bio Elec':   '#1b5e20',  # very dark green
    'Biomass CO2 for Bio H2':     '#2e7d32',  # dark green
    'Biomass CO2 for Bio LF':     '#388e3c',  # medium-dark green
    'Biomass CO2 for Bio NG':     '#66bb6a',  # medium green
    # Bio Ethanol — yellow family
    'Biomass CO2 for Bio Ethanol':'#f9a825',  # dark amber-yellow
    'Bio Ethanol Plant Emissions':'#ffee58',  # bright yellow
    # DAC — navy
    'DAC Emissions':              '#0d1b5e',  # navy
    # NG-related — red family (fossil dark, CCS reductions lighter)
    'Conventional NG':            '#b71c1c',  # very dark red
    'NG Reduction from Power CCS':'#e53935',  # medium red
    'NG Reduction from H2 CCS':   '#ef9a9a',  # light red
    'NG Reduction from DAC CCS':  '#ffcdd2',  # very light red
    # Fossil liquid fuels — dark grey family
    'Conventional Gasoline':      '#424242',  # very dark grey
    'Conventional Jetfuel':       '#616161',  # dark grey
    'Conventional Diesel':        '#9e9e9e',  # medium grey
    # Power — deep orange
    'Power Emissions':            '#e65100',
    # H2 — blue
    'H2 Emissions':               '#0d47a1',
    # Bio process emissions (non-ethanol) — amber/brown family
    'Bio Elec Plant Emissions':   '#ffe082',  # light amber
    'Bio H2 Plant Emissions':     '#ffb300',  # amber
    'Bio LF Plant Emissions':     '#ff8f00',  # dark amber
    'Bio NG Plant Emissions':     '#a5360c',  # brown-orange
    'Bio NG':                     '#bf360c',  # deep burnt orange
    # Bio liquid fuel emissions — teal/cyan family
    'Bio Gasoline':               '#006064',  # very dark teal
    'Bio Jetfuel':                '#00838f',  # dark teal
    'Bio Diesel':                 '#4dd0e1',  # light cyan
    # Synthetic — purple/indigo family
    'Syn NG Plant Emissions':     '#4a148c',  # very dark purple
    'Synthetic NG':               '#7b1fa2',  # dark purple
    'Synfuel Plant Emissions':    '#ab47bc',  # medium purple
    'Syn Gasoline':               '#4527a0',  # dark indigo
    'Syn Jetfuel':                '#5e35b1',  # medium indigo
    'Syn Diesel':                 '#9575cd',  # light indigo
    # Ethylene — pink/magenta
    'Ethylene Production':        '#880e4f',  # very dark pink
    'Ethylene Combustion':        '#e91e63',  # bright pink
}

category_names = {
    'Biomass CO2 for Bio Elec':   'Biomass (Bio Elec)',
    'Biomass CO2 for Bio H2':     'Biomass (Bio H2)',
    'Biomass CO2 for Bio LF':     'Biomass (Bio LF)',
    'Biomass CO2 for Bio NG':     'Biomass (Bio NG)',
    'Biomass CO2 for Bio Ethanol':'Biomass (Bio Ethanol)',
    'DAC Emissions':              'DAC Emissions',
    'NG Reduction from DAC CCS':  'NG Red. (DAC CCS)',
    'NG Reduction from Power CCS':'NG Red. (Power CCS)',
    'NG Reduction from H2 CCS':   'NG Red. (H2 CCS)',
    'Conventional NG':            'Fossil NG',
    'Conventional Gasoline':      'Fossil Gasoline',
    'Conventional Jetfuel':       'Fossil Jetfuel',
    'Conventional Diesel':        'Fossil Diesel',
    'Power Emissions':            'Power Emissions',
    'H2 Emissions':               'H2 Emissions',
    'Bio Elec Plant Emissions':   'Bio Elec Emissions',
    'Bio H2 Plant Emissions':     'Bio H2 Emissions',
    'Bio LF Plant Emissions':     'Bio LF Emissions',
    'Bio NG Plant Emissions':     'Bio NG Emissions',
    'Bio Ethanol Plant Emissions':'Bio Ethanol Emissions',
    'Bio NG':                     'Bio NG',
    'Bio Gasoline':               'Bio Gasoline',
    'Bio Jetfuel':                'Bio Jetfuel',
    'Bio Diesel':                 'Bio Diesel',
    'Syn NG Plant Emissions':     'Syn NG Emissions',
    'Synthetic NG':               'Synthetic NG',
    'Synfuel Plant Emissions':    'Synfuel Emissions',
    'Syn Gasoline':               'Syn Gasoline',
    'Syn Jetfuel':                'Syn Jetfuel',
    'Syn Diesel':                 'Syn Diesel',
    'Ethylene Production':        'Ethylene Production',
    'Ethylene Combustion':        'Ethylene Combustion',
}

plt.rcParams['font.family'] = 'Arial'

# Plotting the combined stacked horizontal bar chart with custom colors
fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
combined_data.plot(kind='barh', stacked=True, width=0.7, ax=ax,
                   color=[category_colors.get(col, '#333333') for col in combined_data.columns])
plt.ylabel('Scenario', fontsize=16)
plt.title('CO2 Emission Balance (Mt)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)

ax.set_xticks([-1500, -750, 0, 750, 1500])

# Set x-axis limits
ax.set_xlim(-1750, 1750)
ax.invert_yaxis()

# Add a vertical line at x=0
ax.axvline(x=0, color='black', linewidth=1, linestyle='--')

handles, labels = ax.get_legend_handles_labels()
labels = [category_names.get(l, l) for l in labels]
ax.legend(handles, labels, bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=10, frameon=False)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version — hover to see individual category values
# ---------------------------------------------------------------------------
fig_plotly = go.Figure()

for col in combined_data.columns:
    display_name = category_names.get(col, col)
    color = category_colors.get(col, '#333333')
    values = combined_data[col].tolist()
    scenarios = combined_data.index.tolist()
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=scenarios,
        x=values,
        orientation='h',
        marker_color=color,
        hovertemplate='%{fullData.name}: %{x:.2f} Mt<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='CO2 Emission Balance (Mt) — Interactive',
    xaxis_title='Mt CO2',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(combined_data)-0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(300, 80 * len(combined_data)),
)
html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_emission_interactive.html')
fig_plotly.write_html(html_path)
webbrowser.open(f'file://{html_path}')

# Print flow summary for each scenario
print()
for scenario in combined_data.index:
    row = combined_data.loc[scenario]
    pos_sum = row[row > 0].sum()
    neg_sum = row[row < 0].sum()
    net_sum = row.sum()
    row_total = annualsum_row_totals.get(scenario, float('nan'))
    print(f'Scenario: {scenario}')
    print(f'  AnnualSum row total : {row_total:+.2f} Mt')
    print(f'  Plot net            : {net_sum:+.2f} Mt  (pos: {pos_sum:+.2f} Mt,  neg: {neg_sum:+.2f} Mt)')
    print()