#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Step_1_Process_Macro_Flows_and_Balance_Demand import (
    dolphyn_base_dir, macro_base_dir,
    dolphyn_results_folder, scenario_names,
)

# ---------------------------------------------------------------------
# Scenario path configuration
# ---------------------------------------------------------------------
# Keys match scenario_names from Step_1.
# Dolphyn paths are relative to dolphyn_base_dir; costs.csv lives at the
# root of the results folder (not in a sector subfolder).
# Macro paths are relative to macro_base_dir.

dolphyn_scenario_paths = {
    "1": f'ethylene_only_test/{dolphyn_results_folder}',
}

macro_scenario_paths = {
    "1": f"6_15_168_restart/results_102/results",
}

# ---------------------------------------------------------------------
# Load costs
# ---------------------------------------------------------------------

def load_macro_cost(scenario):
    path = os.path.join(macro_base_dir, macro_scenario_paths[scenario], "costs.csv")
    df = pd.read_csv(path)
    return float(df["DiscountedTotalCost"].iloc[0])


def load_dolphyn_cost(scenario):
    path = os.path.join(dolphyn_base_dir, dolphyn_scenario_paths[scenario], "costs.csv")
    df = pd.read_csv(path)
    row = df[df["Costs"] == "cTotal"]
    return float(row["Total"].iloc[0])


# ---------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------

print(f"\n{'Scenario':<12} {'Macro Cost ($)':<22} {'Dolphyn Cost ($)':<22} {'% Difference':>14}")
print("-" * 72)

for scenario in scenario_names:
    if scenario not in macro_scenario_paths or scenario not in dolphyn_scenario_paths:
        print(f"{scenario:<12} {'(no path configured)'}")
        continue

    macro_cost = load_macro_cost(scenario)
    dolphyn_cost = load_dolphyn_cost(scenario)

    # % difference relative to Dolphyn: (Macro - Dolphyn) / Dolphyn * 100
    pct_diff = (macro_cost - dolphyn_cost) / dolphyn_cost * 100

    print(
        f"{scenario:<12} "
        f"{macro_cost:>21,.2f}  "
        f"{dolphyn_cost:>21,.2f}  "
        f"{pct_diff:>+13.2f}%"
    )

print()
