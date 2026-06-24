import glob
import os
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.append(REPO_ROOT)
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, macro_scenario_paths

# (subfolder, filename prefix, last column letter to keep from lc_summary)
SOURCE_SPECS = [
    ("bio_ethylene_lcoe",    "LCOE_BIO_ETHYLENE_", "Q"),
    ("sc_esc_ethylene_lcoe", "LCOE_SC_ESC_",       "M"),
    ("synthetic_ethylene",   "LCOE_SYNTHETIC_",    "L"),
]

HEADER_ROW = 1  # 0-indexed -> Excel row 2 (row 1 is a title row)
ID_COL = "id_LC"
SORT_COL = "LCOE ($/t-ethylene)"
DEMAND_DUAL_ID = "ethylene_demand_global"


def col_letter_to_idx(letter):
    """Converts an Excel column letter ('A', 'Q', 'AA', ...) to a 0-indexed column index."""
    idx = 0
    for ch in letter:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def find_case_files():
    """
    Returns {case: [(path, last_col_letter), ...]} by globbing each technology's
    folder for files matching its filename prefix.
    """
    case_files = {}
    for subdir, prefix, last_col_letter in SOURCE_SPECS:
        pattern = os.path.join(SCRIPT_DIR, subdir, f"{prefix}*.csv")
        for path in sorted(glob.glob(pattern)):
            case = Path(path).stem[len(prefix):]
            case_files.setdefault(case, []).append((path, last_col_letter))
    return case_files


def read_case_csv(path, last_col_letter):
    """
    Reads columns A:last_col_letter of a technology's lc_summary CSV, dropping
    rows with id_LC == 0 or any missing value in the kept columns.
    """
    df = pd.read_csv(path, header=HEADER_ROW)
    df = df.iloc[:, : col_letter_to_idx(last_col_letter) + 1]

    df = df.dropna(how="any")
    df = df[~df[ID_COL].astype(str).str.strip().isin(["0", "0.0"])]

    df.insert(0, "source_file", Path(path).name)
    return df.reset_index(drop=True)


def move_col_to_end(df, col):
    """Reorders columns so `col` is the rightmost column, if present."""
    if col in df.columns:
        df = df[[c for c in df.columns if c != col] + [col]]
    return df


def get_ethylene_demand_dual(case):
    """
    Returns the average 'ethylene_demand_global' dual ($/t-ethylene) from the
    case's balance_duals.csv (original MACRO results), or None if the
    scenario/file/column isn't available.
    """
    scenario_path = macro_scenario_paths.get(case)
    if scenario_path is None:
        return None

    duals_path = os.path.join(macro_base_dir, scenario_path, "balance_duals.csv")
    if not os.path.exists(duals_path):
        return None

    duals_df = pd.read_csv(duals_path)
    if DEMAND_DUAL_ID not in duals_df.columns:
        return None

    return round(duals_df[DEMAND_DUAL_ID].mean(), 6)


def main():
    case_files = find_case_files()
    if not case_files:
        print("No LCOE_*.csv files found in bio_ethylene_lcoe/, sc_esc_ethylene_lcoe/, or synthetic_ethylene/")
        return

    for case, file_specs in sorted(case_files.items()):
        print(f"\n=== Case {case}: combining {len(file_specs)} file(s) ===")

        frames = []
        for path, last_col_letter in file_specs:
            df = read_case_csv(path, last_col_letter)
            print(f"  Loaded {Path(path).name}: {df.shape[0]} rows after filtering")
            frames.append(df)

        dual_value = get_ethylene_demand_dual(case)
        if dual_value is not None:
            frames.append(pd.DataFrame([{
                "source_file": "balance_duals.csv",
                ID_COL: DEMAND_DUAL_ID,
                SORT_COL: dual_value,
            }]))
            print(f"  Added {DEMAND_DUAL_ID} dual: {dual_value}")
        else:
            print(f"  WARNING: could not find {DEMAND_DUAL_ID} dual for case {case}")

        combined = pd.concat(frames, axis=0, join="outer", ignore_index=True)
        combined[SORT_COL] = pd.to_numeric(combined[SORT_COL], errors="coerce")
        combined = combined.sort_values(SORT_COL, ascending=True, na_position="last").reset_index(drop=True)
        combined = move_col_to_end(combined, SORT_COL)
    

        out_path = os.path.join(SCRIPT_DIR, f"{case}_ethylene_combined.csv")
        combined.to_csv(out_path, index=False)
        print(f"  Wrote {out_path} ({combined.shape[0]} rows, {combined.shape[1]} columns)")


if __name__ == "__main__":
    main()