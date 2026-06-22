import argparse
import glob
import sys
from pathlib import Path

import pandas as pd
# ─────────────────────────────────────────────────────────────────────────────
# Edit these paths if you prefer not to use command-line arguments
HARDCODED_FILES = [
    r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/bio_ethylene_lcoe/LCOE_BIO_Ethylene.xlsx",
    r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/sc_esc_ethylene_lcoe/LCOE_SC_ESC_Ethylene.xlsx",
    #r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/synthetic_ethylene_lcoe/LCOE_SYNTHETIC_Ethylene.xlsx",
]
HARDCODED_OUTPUT = (
    r"/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/lc_summary_combined.xlsx"
)
# ─────────────────────────────────────────────────────────────────────────────

SHEETS = ["lc_summary_seq", "lc_summary_noseq"]
HEADER_ROW = 1      # 0-indexed row where column names live
DATA_START_ROW = 2  # 0-indexed row where data starts
SORT_COL = "LCOE ($/t-ethylene)"


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def clean_headers(header_row):
    """
    Cleans and standardizes column headers:
    - Forward-fills merged or blank cells.
    - Converts all headers to strings.
    - Strips whitespace and normalizes spacing.
    - Ensures unique column names.
    """
    headers = (
        pd.Series(header_row)
        .ffill()  # Handle merged/blank header cells
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"\.0$", "", regex=True)  # Remove trailing .0 from numeric headers
    )

    # Ensure unique column names
    seen = {}
    unique_headers = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_headers.append(h)

    #print(type(unique_headers), unique_headers)

    return unique_headers


def read_sheet(path, sheet):
    """
    Reads a specified sheet from an Excel file and returns a cleaned DataFrame.
    """
    try:
        raw = pd.read_excel(path, sheet_name=sheet, header=None)
    except Exception as e:
        print(f"  WARNING: could not read '{sheet}' from '{path}': {e}")
        return None

    # Drop columns that are entirely empty
    raw = raw.dropna(axis=1, how="all")

    # Ensure the header row exists
    if len(raw) <= HEADER_ROW:
        print(f"  WARNING: '{sheet}' in '{path}' does not contain the expected header row.")
        return None

    # Clean and assign headers
    headers = clean_headers(raw.iloc[HEADER_ROW])
    data = raw.iloc[DATA_START_ROW:].copy()
    data.columns = headers

    # Replace empty strings or whitespace with NaN and drop empty rows
    data = data.replace(r"^\s*$", pd.NA, regex=True)
    data = data.dropna(how="all")

    # ------------------------------------------------------------------
    # Remove unwanted constant columns from BIOETHYLENE files
    # ------------------------------------------------------------------
    columns_to_remove = {"Ethylene LHV", "45.6", "GJ/t-ethylene"}
    existing_cols = [col for col in columns_to_remove if col in data.columns]
    if existing_cols:
        data = data.drop(columns=existing_cols)
        print(f"  Dropped columns from {Path(path).name} ({sheet}): {existing_cols}")

    # Add a column to track the source file
    data.insert(0, "source_file", Path(path).name)

    return data.reset_index(drop=True)


def concat_sheets(paths, sheet):
    """
    Concatenates a specific sheet from multiple Excel files using an outer join.
    """
    frames = []
    for path in paths:
        df = read_sheet(path, sheet)
        if df is not None and not df.empty:
            frames.append(df)
            print(f"  Loaded '{sheet}' from {Path(path).name} with shape {df.shape}")
        else:
            print(f"  No usable data in '{sheet}' from {Path(path).name}")

    if not frames:
        print(f"  No data found for sheet '{sheet}'.")
        return pd.DataFrame()

    return pd.concat(frames, axis=0, join="outer", ignore_index=True)


def sort_df(df):
    """
    Sorts the DataFrame by the specified LCOE column if present.
    """
    if SORT_COL in df.columns:
        df[SORT_COL] = pd.to_numeric(df[SORT_COL], errors="coerce")
        df = df.sort_values(SORT_COL, ascending=True, na_position="last")
    else:
        print(f"  WARNING: sort column '{SORT_COL}' not found; output will not be sorted.")
    return df.reset_index(drop=True)


def write_output(dfs, output_path):
    """
    Writes the resulting DataFrames to an Excel file with separate sheets.
    """
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            if df.empty:
                pd.DataFrame([["No data found"]]).to_excel(
                    writer, sheet_name=sheet_name, index=False, header=False
                )
            else:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\nOutput written to: {output_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="*", help="xlsx file paths (supports globs)")
    parser.add_argument(
        "-o", "--output", default="lc_summary_combined.xlsx",
        help="Output Excel file path"
    )
    args = parser.parse_args()

    # Determine input files and output path
    raw_patterns = HARDCODED_FILES if HARDCODED_FILES else args.files
    output_path = HARDCODED_OUTPUT if HARDCODED_OUTPUT else args.output

    # Expand glob patterns
    paths = []
    for pattern in raw_patterns:
        expanded = glob.glob(pattern)
        paths.extend(expanded if expanded else [pattern])
    paths = sorted(set(paths))

    if not paths:
        print("ERROR: No input files found. Add paths to HARDCODED_FILES or pass them as arguments.")
        sys.exit(1)

    print(f"Processing {len(paths)} file(s):")
    for p in paths:
        print(f"  {p}")

    # Process each sheet
    result = {}
    for sheet in SHEETS:
        print(f"\n--- Processing sheet: {sheet} ---")
        df = concat_sheets(paths, sheet)
        df = sort_df(df)
        print(f"  Combined shape: {df.shape}")
        result[sheet] = df

    # Write output
    write_output(result, output_path)


if __name__ == "__main__":
    main()