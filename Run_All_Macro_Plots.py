#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run all Macro Plots Codes scripts and display their figures in a grid.
The individual scripts are NOT modified — plt.show is temporarily intercepted
to capture each figure as an image before assembling the grid.
"""

import importlib.util
import os
import sys
from io import BytesIO, StringIO

import matplotlib.pyplot as plt

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Macro Plots Codes")

SCRIPT_FILES = [
    "Power_Macro.py",
    "H2_Macro.py",
    "NG_Macro.py",
    "LF_Macro.py",
    "CO2_Capture_Macro.py",
    "CO2_Emission_Macro.py",
    "ETHYLENE_Macro.py",
    "ETHANOL_Macro.py",
]

GRID_COLS = 4
DPI = 150

# -------------------------------------------------------------------------
# Capture figures from each script
# -------------------------------------------------------------------------

captured_images = []   # list of PNG arrays
captured_titles = []   # label for each panel
captured_output = []   # stdout text from each script

original_show = plt.show

def _capture_show(*args, **kwargs):
    fig = plt.gcf()
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=DPI)
    buf.seek(0)
    captured_images.append(plt.imread(buf))
    plt.close(fig)

plt.show = _capture_show

for script_name in SCRIPT_FILES:
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(script_path):
        print(f"Warning: {script_name} not found, skipping.")
        continue

    label = script_name.replace("_Macro.py", "").replace("_", " ")
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
    except Exception as exc:
        sys.stdout = sys.__stdout__
        print(f"  ERROR in {script_name}: {exc}")

plt.show = original_show

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

plt.tight_layout(pad=0.5)
plt.show()
