"""
Run all Macro Plots Codes scripts and display their figures in a grid.
The individual scripts are NOT modified — plt.show is temporarily intercepted
to capture each figure as an image before assembling the grid.
"""

import html as _html
import importlib.util
import os 
import sys
import webbrowser
from io import BytesIO, StringIO

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html as _pio_to_html
from plotly.subplots import make_subplots

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Macro Plots Codes")

SCRIPT_FILES = [
    "Power_Macro.py",
    "Power_Macro_byZone.py",
    "H2_Macro.py",
    "H2_Macro_byZone.py",
    "NG_Macro.py",
    "NG_Macro_byZone.py",
    "LF_Macro.py",
    "LF_Macro_byZone.py",
    "CO2_Capture_Macro.py",
    "CO2_Emission_Macro.py",
    "ETHYLENE_Macro.py",
    "ETHYLENE_Macro_byZone.py",
    "ETHANOL_Macro.py",
    "ETHANOL_Macro_byZone.py",
]

GRID_COLS = 4
DPI = 150

# -------------------------------------------------------------------------
# Capture figures from each script
# -------------------------------------------------------------------------

captured_images = []   # list of PNG arrays
captured_titles = []   # label for each panel
captured_output = []   # stdout text from each script
plotly_figs   = []   # fig_plotly objects from each script
plotly_titles = []   # matching labels

original_show = plt.show
original_browser_open = webbrowser.open

def _capture_show(*args, **kwargs):
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=DPI)
    buf.seek(0)
    captured_images.append(plt.imread(buf))
    plt.close(fig)

plt.show = _capture_show
webbrowser.open = lambda *a, **kw: None  # suppress individual HTML opens

for script_name in SCRIPT_FILES:
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"Warning: {script_name} not found, skipping.")
        continue

    label = (
        script_name.replace(".py", "")
        .replace("_Macro", "")
        .replace("byZone", "by Zone")
        .replace("_", " ")
    )
    print(f"Running {script_name} ...")

    spec = importlib.util.spec_from_file_location(
        script_name.replace(".py", ""), script_path
    )
    module = importlib.util.module_from_spec(spec)
    module.__file__ = script_path  # ensure the script's own __file__ is correct

    buf = StringIO()
    sys.stdout = buf
    try:
        spec.loader.exec_module(module)
        sys.stdout = sys.__stdout__
        captured_titles.append(label)
        captured_output.append((label, buf.getvalue()))
        if hasattr(module, 'fig_plotly'):
            plotly_figs.append(module.fig_plotly)
            plotly_titles.append(label)
        if hasattr(module, 'extra_plotly_figs'):
            for _xfig, _xtitle in zip(module.extra_plotly_figs, module.extra_plotly_titles):
                plotly_figs.append(_xfig)
                plotly_titles.append(f"{label} – {_xtitle}")
    except Exception as exc:
        sys.stdout = sys.__stdout__
        print(f"  ERROR in {script_name}: {exc}")

plt.show = original_show
webbrowser.open = original_browser_open

# -------------------------------------------------------------------------
# Print all balance summaries together
# -------------------------------------------------------------------------

def _extract_balance_check(text):
    lines = text.splitlines()
    result = []
    in_check = False
    for line in lines:
        if "balance check:" in line.lower():
            in_check = True
            result.append(line)
        elif in_check:
            if line.startswith("  ") or line.startswith("\t"):
                result.append(line)
            else:
                in_check = False
    return "\n".join(result)

print("\n" + "=" * 60)
print("  BALANCE CHECK SUMMARY — ALL SECTORS")
print("=" * 60)
for label, output in captured_output:
    summary = _extract_balance_check(output)
    if summary:
        print(summary)
print("=" * 60 + "\n")

# -------------------------------------------------------------------------
# Assemble grid
# -------------------------------------------------------------------------

n = len(captured_images)
if n == 0:
    print("No figures captured.")
    sys.exit(1)

cols = min(GRID_COLS, n)
rows = (n + cols - 1) // cols

fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 4.5))
axes = [axes] if n == 1 else list(axes.flatten())

for i, (img, title) in enumerate(zip(captured_images, captured_titles)):
    axes[i].imshow(img)
    axes[i].axis("off")

# Hide any unused subplot slots
for j in range(n, len(axes)):
    axes[j].axis("off")

# -------------------------------------------------------------------------
# Economic / dual charts — costs, CO2 shadow price, commodity duals
# -------------------------------------------------------------------------

_s1 = sys.modules.get('Step_1_Process_Macro_Flows_and_Balance_Demand')
if _s1 is not None:
    _base       = _s1.macro_base_dir
    _scen_paths = _s1.macro_scenario_paths
    _scen_names = _s1.scenario_names

    # ── 1. Discounted costs: capex + variable ──────────────────────────
    _capex, _var = [], []
    for _scen in _scen_names:
        _p = os.path.join(_base, _scen_paths.get(_scen, ''), 'costs.csv')
        try:
            _df = pd.read_csv(_p)
            _df.columns = _df.columns.str.strip()
            _capex.append(float(_df['DiscountedFixedCost'].iloc[0]) * 1e-9)
            _var.append(float(_df['DiscountedVariableCost'].iloc[0]) * 1e-9)
        except Exception as _e:
            print(f"  Warning: costs.csv missing for scenario {_scen}: {_e}")
            _capex.append(None)
            _var.append(None)

    if any(v is not None for v in _capex):
        _fig_cost = go.Figure()
        _fig_cost.add_trace(go.Bar(
            name='Capex (Fixed)', y=_scen_names, x=_capex,
            orientation='h', marker_color='steelblue',
            hovertemplate='Capex: $%{x:.2f}B<extra></extra>',
        ))
        _fig_cost.add_trace(go.Bar(
            name='Variable Cost', y=_scen_names, x=_var,
            orientation='h', marker_color='coral',
            hovertemplate='Variable: $%{x:.2f}B<extra></extra>',
        ))
        _fig_cost.update_layout(
            barmode='stack',
            title='Discounted Total Cost (Billion $)',
            xaxis_title='Billion $',
            yaxis=dict(autorange='reversed'),
            legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
            height=max(400, 80 * len(_scen_names)),
        )
        plotly_figs.append(_fig_cost)
        plotly_titles.append('Cost')

    # ── 2. CO2 cap shadow price ────────────────────────────────────────
    _co2_vals = []
    for _scen in _scen_names:
        _p = os.path.join(_base, _scen_paths.get(_scen, ''), 'co2_cap_duals.csv')
        try:
            _df = pd.read_csv(_p)
            _df.columns = _df.columns.str.strip()
            _pcol = next(
                (c for c in _df.columns if 'shadow' in c.lower() or 'price' in c.lower()),
                None,
            )
            _co2_vals.append(float(_df[_pcol].iloc[0]) if _pcol else None)
        except Exception as _e:
            print(f"  Warning: co2_cap_duals.csv missing for scenario {_scen}: {_e}")
            _co2_vals.append(None)

    if any(v is not None for v in _co2_vals):
        _fig_co2d = go.Figure()
        _fig_co2d.add_trace(go.Bar(
            name='CO2 Shadow Price', y=_scen_names, x=_co2_vals,
            orientation='h', marker_color='darkblue',
            hovertemplate='CO2 Price: $%{x:.2f}/t<extra></extra>',
        ))
        _fig_co2d.update_layout(
            title='CO2 Cap Shadow Price',
            xaxis_title='$/tonne CO2',
            yaxis=dict(autorange='reversed'),
            height=max(400, 80 * len(_scen_names)),
        )
        plotly_figs.append(_fig_co2d)
        plotly_titles.append('CO2 Cap Dual')

    # ── 3. Balance duals: average across zones and time ────────────────
    # Values ≥ 1e6 are big-M penalty prices and are excluded from the mean.
    _PENALTY = 1e6
    _ZONE_LIST = ["CA", "NW", "SW", "TX", "NCEN", "CEN", "SE", "MIDAT", "NE"]
    _dual_by_scen = {}
    _zonal_dual_by_scen = {}
    for _scen in _scen_names:
        _p = os.path.join(_base, _scen_paths.get(_scen, ''), 'balance_duals.csv')
        try:
            _df = pd.read_csv(_p)

            # Aggregate view: average each commodity across all its locations.
            _comm_groups = {}
            for _col in _df.columns:
                _comm_groups.setdefault(_col.rsplit('_', 1)[0], []).append(_col)
            _dual_by_scen[_scen] = {}
            for _comm, _cols in _comm_groups.items():
                _vals = _df[_cols].values.flatten().astype(float)
                _vals = _vals[_vals < _PENALTY]
                _dual_by_scen[_scen][_comm] = float(_vals.mean()) if len(_vals) else None

            # Zonal view: per-zone mean for commodities with one column per zone.
            _zone_comm_groups = {}
            for _col in _df.columns:
                _prefix, _, _suffix = _col.rpartition('_')
                if _suffix in _ZONE_LIST:
                    _zone_comm_groups.setdefault(_prefix, {})[_suffix] = _col
            _zonal_dual_by_scen[_scen] = {}
            for _comm, _zone_cols in _zone_comm_groups.items():
                if set(_zone_cols) != set(_ZONE_LIST):
                    continue  # skip commodities with incomplete zone coverage
                _zone_means = {}
                for _zone, _col in _zone_cols.items():
                    _vals = _df[_col].values.astype(float)
                    _vals = _vals[_vals < _PENALTY]
                    _zone_means[_zone] = float(_vals.mean()) if len(_vals) else None
                _zonal_dual_by_scen[_scen][_comm] = _zone_means
        except Exception as _e:
            print(f"  Warning: balance_duals.csv missing for scenario {_scen}: {_e}")
            _dual_by_scen[_scen] = {}
            _zonal_dual_by_scen[_scen] = {}

    _all_comms = sorted({c for d in _dual_by_scen.values() for c in d})
    if _all_comms:
        _pal = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        _fig_duals = go.Figure()
        for _i, _scen in enumerate(_scen_names):
            _fig_duals.add_trace(go.Bar(
                name=f'Scenario {_scen}',
                y=_all_comms,
                x=[_dual_by_scen.get(_scen, {}).get(_c) for _c in _all_comms],
                orientation='h',
                marker_color=_pal[_i % len(_pal)],
                hovertemplate='%{y}: %{x:.2f}<extra>Scen. ' + _scen + '</extra>',
            ))
        _fig_duals.update_layout(
            barmode='group',
            title='Average Balance Duals by Commodity (penalty values ≥ 1e6 excluded)',
            xaxis_title='Avg. Dual ($/unit)',
            legend=dict(orientation='v', x=1.02, y=1, xanchor='left'),
            height=max(500, 30 * len(_all_comms)),
        )
        plotly_figs.append(_fig_duals)
        plotly_titles.append('Commodity Duals')

    # ── 4. Commodity duals by zone: one subplot grid per scenario ───────
    _zonal_commodities = sorted({
        _comm
        for _scen_duals in _zonal_dual_by_scen.values()
        for _comm in _scen_duals
    })

    if _zonal_commodities:
        _grid_cols = 4
        _grid_rows = (len(_zonal_commodities) + _grid_cols - 1) // _grid_cols

        for _scen in _scen_names:
            _scen_duals = _zonal_dual_by_scen.get(_scen, {})
            if not _scen_duals:
                continue

            _fig_zonal = make_subplots(
                rows=_grid_rows,
                cols=_grid_cols,
                subplot_titles=[c.replace('_', ' ').title() for c in _zonal_commodities],
            )

            for _i, _comm in enumerate(_zonal_commodities):
                _row = _i // _grid_cols + 1
                _col_pos = _i % _grid_cols + 1
                _zone_means = _scen_duals.get(_comm, {})
                _fig_zonal.add_trace(
                    go.Bar(
                        x=_ZONE_LIST,
                        y=[_zone_means.get(_z) for _z in _ZONE_LIST],
                        marker_color='teal',
                        showlegend=False,
                        hovertemplate='%{x}: %{y:.2f}<extra>' + _comm + '</extra>',
                    ),
                    row=_row,
                    col=_col_pos,
                )

            _fig_zonal.update_xaxes(tickangle=45, tickfont_size=9)
            _fig_zonal.update_yaxes(tickfont_size=9)
            _fig_zonal.update_layout(
                title=f'Balance Duals by Zone — Scenario {_scen} (penalty values ≥ 1e6 excluded)',
                height=max(700, 260 * _grid_rows),
                showlegend=False,
            )
            plotly_figs.append(_fig_zonal)
            plotly_titles.append(f'Commodity Duals by Zone — Scenario {_scen}')
else:
    print("Warning: Step_1 module not in sys.modules; skipping cost/dual charts.")

# -------------------------------------------------------------------------
# Combine all Plotly figures into one interactive HTML page
# (opened before plt.show() so both appear at the same time)
# -------------------------------------------------------------------------

if plotly_figs:
    balance_by_label = {
        label: _extract_balance_check(output)
        for label, output in captured_output
    }

    html_parts = [
        '<html><head>',
        '<style>',
        '  body { font-family: Arial, sans-serif; margin: 30px; background: #fff; }',
        '  h1 { font-size: 22px; border-bottom: 2px solid #333; padding-bottom: 8px; }',
        '  h2 { font-size: 16px; color: #444; margin-top: 40px; }',
        '  .plot-section { margin-bottom: 50px; }',
        '  .balance-summary { font-family: monospace; font-size: 13px; color: #333;',
        '    background: #f5f5f5; border: 1px solid #ddd; padding: 10px 14px;',
        '    border-radius: 4px; margin-top: 8px; white-space: pre; display: inline-block; }',
        '</style>',
        '</head><body>',
        '<h1>MACRO Results by Sector</h1>',
    ]

    for i, (title, fig) in enumerate(zip(plotly_titles, plotly_figs)):
        html_parts.append(f'<div class="plot-section"><h2>{title}</h2>')
        html_parts.append(
            _pio_to_html(fig, include_plotlyjs=(i == 0), full_html=False, div_id=f'macro_plot_{i}')
        )
        balance_text = balance_by_label.get(title, '')
        if balance_text:
            html_parts.append(f'<div class="balance-summary">{_html.escape(balance_text)}</div>')
        html_parts.append('</div>')

    html_parts.append('</body></html>')

    combined_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'macro_all_interactive.html')
    with open(combined_path, 'w') as _f:
        _f.write('\n'.join(html_parts))

    webbrowser.open(f'file://{combined_path}')
    print(f"\nCombined interactive HTML: {combined_path}")

plt.tight_layout(pad=0.5)
plt.show()
