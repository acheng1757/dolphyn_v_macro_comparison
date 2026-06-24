import os
import sys
from pathlib import Path

import pandas as pd
import xlwings as xw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.append(REPO_ROOT)
from Step_1_Process_Macro_Flows_and_Balance_Demand import scenario_names

# ─────────────────────────────────────────────────────────────────────────────
# Edit these if a pipeline's output folder/filename pattern or column range changes
# (subfolder, filename template, last column letter to read from lc_summary)
SOURCE_FILES = [
    ("bio_ethylene_lcoe",    "LCOE_BIO_ETHYLENE_{label}.xlsx", "Q"),
    ("sc_esc_ethylene_lcoe", "LCOE_SC_ESC_{label}.xlsx",       "M"),
    ("synthetic_ethylene",   "LCOE_SYNTHETIC_{label}.xlsx",    "M"),
]
# ─────────────────────────────────────────────────────────────────────────────

SHEET = "lc_summary"
HEADER_ROW = 1      # 0-indexed row where column names live (Excel row 2)
DATA_START_ROW = 2  # 0-indexed row where data starts (Excel row 3)
SORT_COL = "LCOE ($/t-ethylene)"


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def col_letter_to_idx(letter):
    """Converts an Excel column letter ('A', 'Q', 'AA', ...) to a 0-indexed column index."""
    idx = 0
    for ch in letter:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def recalculate_workbooks(paths):
    """
    lc_summary/lc_detailed cells are formulas; openpyxl never evaluates them, so
    values written by the upstream pipeline scripts sit uncalculated until a real
    spreadsheet engine recomputes them. Drive actual Excel to recalculate and
    resave each workbook before we read it with pandas.
    """
    if not paths:
        return
    app = xw.App(visible=False)
    try:
        for path in paths:
            wb = app.books.open(path)
            app.calculate()
            wb.save()
            wb.close()
            print(f"  Recalculated {Path(path).name}")
    finally:
        app.quit()


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

    return unique_headers


def read_sheet(path, sheet, last_col_letter):
    """
    Reads columns A:last_col_letter of a specified sheet from an Excel file and
    returns a cleaned DataFrame, dropping rows with Excel error values.
    """
    try:
        raw = pd.read_excel(path, sheet_name=sheet, header=None)
    except Exception as e:
        print(f"  WARNING: could not read '{sheet}' from '{path}': {e}")
        return None

    raw = raw.iloc[:, : col_letter_to_idx(last_col_letter) + 1]

    # Drop columns that are entirely empty (e.g. a spacer column within the slice)
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

    # Drop rows containing an Excel error value (#DIV/0!, #REF!, #N/A, ...) in any column
    is_error = data.apply(lambda row: row.astype(str).str.startswith("#").any(), axis=1)
    if is_error.any():
        print(f"  Dropped {is_error.sum()} row(s) with Excel errors from {Path(path).name} ({sheet})")
        data = data[~is_error]

    # Drop placeholder rows (template rows beyond the real asset count: id_LC is 0/blank)
    if "id_LC" in data.columns:
        is_placeholder = data["id_LC"].isna() | (data["id_LC"] == 0)
        if is_placeholder.any():
            print(f"  Dropped {is_placeholder.sum()} placeholder row(s) (id_LC==0/blank) from {Path(path).name} ({sheet})")
            data = data[~is_placeholder]

    # Add a column to track the source file
    data.insert(0, "source_file", Path(path).name)

    return data.reset_index(drop=True)


def concat_sheets(file_specs, sheet):
    """
    Concatenates a specific sheet from multiple Excel files using an outer join.
    file_specs: list of (path, last_col_letter) tuples.
    """
    frames = []
    for path, last_col_letter in file_specs:
        df = read_sheet(path, sheet, last_col_letter)
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


def move_col_to_end(df, col):
    """Reorders columns so `col` is the rightmost column, if present."""
    if col in df.columns:
        df = df[[c for c in df.columns if c != col] + [col]]
    return df


def write_output(dfs, out_dir):
    """
    Writes a "<name>_ethylene_case.csv" per entry to out_dir.
    """
    for sheet_name, df in dfs.items():
        if df.empty:
            print(f"  Skipping {sheet_name}: no data found")
            continue

        df = move_col_to_end(df, SORT_COL)
        csv_path = os.path.join(out_dir, f"{sheet_name}_ethylene_case.csv")
        df.to_csv(csv_path, index=False)
        print(f"  Wrote {csv_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main Execution
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Resolve every (scenario, technology) file path up front
    per_scenario_files = {}
    all_paths = []
    for label in scenario_names:
        file_specs = []
        for subdir, filename_template, last_col_letter in SOURCE_FILES:
            path = os.path.join(SCRIPT_DIR, subdir, filename_template.format(label=label))
            if os.path.exists(path):
                file_specs.append((path, last_col_letter))
                all_paths.append(path)
            else:
                print(f"Warning: {path} not found for scenario {label} (run that pipeline's b_csv_to_xlsx.py/c_duals_to_xlsx.py first)")
        per_scenario_files[label] = file_specs

    print(f"\nRecalculating {len(all_paths)} workbook(s) in Excel before reading...")
    recalculate_workbooks(all_paths)

    result = {}
    for label in scenario_names:
        file_specs = per_scenario_files[label]
        if not file_specs:
            print(f"Skipping scenario {label}: no ethylene LCOE files found")
            continue

        print(f"\n=== Scenario {label}: combining {len(file_specs)} file(s) ===")
        for path, _ in file_specs:
            print(f"  {path}")

        df = concat_sheets(file_specs, SHEET)
        df = sort_df(df)
        print(f"  Combined shape: {df.shape}")
        result[str(label)] = df

    write_output(result, SCRIPT_DIR)


if __name__ == "__main__":
    main()
