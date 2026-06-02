import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go
import webbrowser
import sys

# ---------------------------------------------------------------------
# Global settings
# ---------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import dolphyn_base_dir, dolphyn_results_folder, scenario_names

# List of scenario file paths and scenario names
file_paths = [f'{dolphyn_base_dir}/all_demand_test/{dolphyn_results_folder}/Results_CSC/Zone_CO2_storage_balance.csv']

# Columns of interest for summation
columns_of_interest = ["Power CCS",
                       "H2 CCS",
                       "DAC Capture",
                       "DAC Fuel CCS",
                       "Bio Elec Capture", 
                       "Bio H2 Capture", 
                       "Bio LF Capture", 
                       "Bio NG Capture", 
                       "Synfuel Plant Capture",
                       "Synfuel Plant Consumption",
                       "Syn NG Plant Capture",
                       "Syn NG Plant Consumption",
                       "NG Power CCS",
                       "NG H2 CCS",
                       "NG DAC CCS",
                       "CO2 Storage",
                       "Ethylene Production",
                       "Bio Ethanol Capture",
                       ]


conversion_factor = 1e-6  # Mt

# Initialize a dictionary to store global values for each scenario
global_values_per_scenario = {}
annualsum_row_totals = {}

# Process each file
for path, scenario in zip(file_paths, scenario_names):
    # Load the CSV file
    df = pd.read_csv(path, header=0)

    # Extract the 'AnnualSum' row by searching for it (assuming it's in the second row, index 1)
    annual_sum_row = df[df.iloc[:, 0] == 'AnnualSum']

    if not annual_sum_row.empty:
        # Full row total: sum every numeric column in the AnnualSum row
        annualsum_row_totals[scenario] = (
            annual_sum_row.iloc[:, 1:]
            .apply(pd.to_numeric, errors='coerce')
            .sum(axis=1)
            .values[0] * conversion_factor
        )

        # Select columns of interest and sum across zones
        global_values = {}
        for col in columns_of_interest:
            # Sum across zones for this column and apply unit conversion
            col_values = annual_sum_row.filter(like=col, axis=1).astype(float).sum(axis=1).values * conversion_factor
            global_values[col] = col_values[0] if col_values.size > 0 else 0
    else:
        # Handle case where 'AnnualSum' row is not found
        global_values = {col: 0 for col in columns_of_interest}
        annualsum_row_totals[scenario] = 0.0

    # Store the global values for this scenario
    global_values_per_scenario[scenario] = global_values

# Convert the global values dictionary to a DataFrame for plotting
combined_data = pd.DataFrame(global_values_per_scenario).T  # Transpose for easier plotting

combine_mapping = {
    'NG DAC CCS': 'DAC Capture',
    
    'Bio Elec Capture': 'Biomass Capture',
    'Bio H2 Capture': 'Biomass Capture',
    'Bio LF Capture': 'Biomass Capture',
    'Bio NG Capture': 'Biomass Capture',

    'Syn NG Plant Capture': 'Synthetic NG',
    'Syn NG Plant Consumption': 'Synthetic NG',
    
    'Synfuel Plant Capture': 'Synthetic Fuels',
    'Synfuel Plant Consumption': 'Synthetic Fuels',

    'Bio Ethanol Capture': 'Bio Ethanol Capture',

    'Ethylene Production' : 'Ethylene Production',
}

# Apply the mapping to combine categories in the columns
combined_data = combined_data.rename(columns=combine_mapping)

# Group the combined data by the new category names and sum the values
combined_data = combined_data.groupby(by=combined_data.columns, axis=1).sum()

# Custom order for arranging categories
desired_order = [
    'CO2 Storage',
    'Synthetic Fuels',
    'Synthetic NG',
    'NG Power CCS',
    'Power CCS',
    'NG H2 CCS',
    'H2 CCS',
    'DAC Capture',
    'DAC Fuel CCS',
    'Biomass Capture',
    'Bio Ethanol Capture',
    'Ethylene Production',
]

# Reorder the columns based on the desired order (only keep the matching columns)
combined_data = combined_data[[col for col in desired_order if col in combined_data.columns]]

# Custom colors and display names
category_colors = {
    'Biomass Capture':  'olivedrab',
    'DAC Capture':      'darkblue',
    'DAC Fuel CCS':     'steelblue',
    'NG Power CCS':     '#e65100',   # deep orange
    'Power CCS':        '#ff8f00',   # lighter orange
    'NG H2 CCS':        '#0d47a1',   # deep blue
    'H2 CCS':           '#42a5f5',   # lighter blue
    'Synthetic Fuels':  'purple',
    'Synthetic NG':     'violet',
    'CO2 Storage':      'darkgoldenrod',
    'Bio Ethanol Capture': '#f5c518',
    'Ethylene Production': 'darkgreen',
}

category_names = {
    'CO2 Storage':         'CO2 Storage',
    'Synthetic NG':        'Syn. NG',
    'Synthetic Fuels':     'Syn. Liquids',
    'NG Power CCS':        'NG Power CCS',
    'Power CCS':           'Power CCS',
    'NG H2 CCS':           'NG H2 CCS',
    'H2 CCS':              'H2 CCS',
    'DAC Capture':         'DAC Capture',
    'DAC Fuel CCS':        'DAC Fuel CCS',
    'Biomass Capture':     'Biomass CCS',
    'Bio Ethanol Capture': 'Bio Ethanol CCS',
    'Ethylene Production': 'Ethylene Production',
}

import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'

# Ensure the column order follows the legend order
desired_order = [col for col in category_names if col in combined_data.columns]
combined_data = combined_data[desired_order]

# Plotting — figure height scales with number of scenarios
n_scenarios = len(combined_data)
fig, ax = plt.subplots(figsize=(12, max(5, n_scenarios * 1.5)), constrained_layout=True)
combined_data.plot(kind='barh', stacked=True, width=0.6, ax=ax,
                   color=[category_colors.get(col, '#333333') for col in combined_data.columns])

# Axis labels and title
plt.ylabel('Scenario', fontsize=16)
plt.xlabel('Mt CO2', fontsize=16)
plt.title('Captured CO2 Balance (Mt)', fontsize=16)
plt.yticks(fontsize=16)
plt.xticks(fontsize=16)

ax.axvline(x=0, color='black', linewidth=1, linestyle='--')
ax.invert_yaxis()

# Custom legend — placed to the right so it doesn't compress the bars
handles, _ = ax.get_legend_handles_labels()
custom_labels = [category_names[col] for col in combined_data.columns]
ax.legend(handles, custom_labels, bbox_to_anchor=(1.02, 1), loc='upper left',
          fontsize=12, frameon=False)

plt.show()

# ---------------------------------------------------------------------------
# Interactive Plotly version
# ---------------------------------------------------------------------------
fig_plotly = go.Figure()

for col in combined_data.columns:
    display_name = category_names.get(col, col)
    color = category_colors.get(col, '#333333')
    fig_plotly.add_trace(go.Bar(
        name=display_name,
        y=combined_data.index.tolist(),
        x=(combined_data[col] * 1e6).tolist(),  # convert Mt → tonnes
        orientation='h',
        marker_color=color,
        hovertemplate='%{fullData.name}: %{x:,.0f} t<extra></extra>',
    ))

fig_plotly.update_layout(
    barmode='relative',
    title='Captured CO2 Balance (tonnes) — Interactive',
    xaxis_title='tonnes CO2',
    yaxis=dict(autorange='reversed'),
    legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
    shapes=[dict(type='line', x0=0, x1=0, y0=-0.5,
                 y1=len(combined_data) - 0.5, yref='y',
                 line=dict(color='black', width=1, dash='dash'))],
    height=max(300, 80 * len(combined_data)),
    xaxis=dict(tickformat=',.0f'),
)

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'co2_capture_interactive.html')
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
    print(f'  AnnualSum row total : {row_total:+.4f} Mt')
    print(f'  Plot net            : {net_sum:+.4f} Mt  (pos: {pos_sum:+.4f} Mt,  neg: {neg_sum:+.4f} Mt)')
    print()
