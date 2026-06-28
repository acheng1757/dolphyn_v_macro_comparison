import json
import csv
import glob
import io
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.append(REPO_ROOT)
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_input_paths


def json_to_csv_transforms(json_data, output_path=None, field_map=None):
    """
    Parse JSON and extract fields per instance.

    Args:
        json_data: dict (already parsed JSON) or str (path to JSON file)
        output_path: optional path to write CSV. If None, prints to stdout.
        field_map: list of (output_col_name, source, json_key) tuples. Fields
                   live directly on the instance dict, so source is always "id"
                   → instance.get(json_key).
    """
    if isinstance(json_data, str):
        with open(json_data) as f:
            json_data = json.load(f)

    output_cols = [col for col, _, _ in field_map]
    rows = []

    for asset_type, asset_list in json_data.items():
        for asset in asset_list:
            for instance in asset.get("instance_data", []):
                row = {
                    col_name: instance.get(json_key)
                    for col_name, _, json_key in field_map
                }
                rows.append(row)

    if output_path:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_cols)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Written to {output_path}")
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=output_cols)
        writer.writeheader()
        writer.writerows(rows)
        print(output.getvalue())

    return rows


# synthetic_ethylene.json: fields live directly on the instance dict
# (no "transforms"/"edges" nesting), same flat layout as CELLULOSIC_FIELD_MAP
# in lcoe/bio_ethanol_lcoe/a_json_to_csv.py.

DEFAULT_FIELD_MAP = [
        ("id",                                          "id",                          "id"),
        ("biomass_commodity",           "id",                  "biomass_commodity"),
        ("co2_content",           "id",                  "co2_content"),
        ("investment_cost",        "id", "investment_cost"),
        ("fixed_om_cost",          "id", "fixed_om_cost"),
        ("variable_om_cost",             "id", "variable_om_cost"),
        ("electricity_consumption",           "id",                  "electricity_consumption"),
        ("gasoline_production", "id",                  "gasoline_production"),
        ("jetfuel_production",             "id",                  "jetfuel_production"),
        ("diesel_production",            "id",                  "diesel_production"),
        ("electricity_production",             "id",                  "electricity_production"),
        ("emission_rate",            "id",                  "emission_rate"),
        ("capture_rate",        "id", "capture_rate"),
    ]

# (json filename in <scenario>/assets/, output csv filename, field_map override)
ASSET_FILES = [
    ("beccs_liquid_fuels.json", "beccs_liquid_fuels.csv", DEFAULT_FIELD_MAP),
]

if __name__ == "__main__":
    # Clear outputs from any previous run before regenerating — case folders
    # created below, plus the downstream LCOE_BIOLF_<case>.csv/.xlsx files
    # produced by b_csv_to_xlsx.py / c_duals_to_xlsx.py. Cases come from
    # scenario_names, which changes over time, so a case removed from there
    # would otherwise leave its old outputs behind forever.
    for entry in os.listdir(SCRIPT_DIR):
        if entry == "__pycache__" or entry.startswith("."):
            continue
        entry_path = os.path.join(SCRIPT_DIR, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)

    for pattern in ("LCOE_BIOLF_*.csv", "LCOE_BIOLF_*.xlsx"):
        for path in glob.glob(os.path.join(SCRIPT_DIR, pattern)):
            if os.path.basename(path) == "LCOE_BIOLF_TEMPLATE.xlsx":
                continue
            os.remove(path)

    for label in scenario_names:
        assets_dir = os.path.join(macro_base_dir, macro_input_paths[label], "assets")
        out_dir = os.path.join(SCRIPT_DIR, label)
        os.makedirs(out_dir, exist_ok=True)

        for json_name, csv_name, field_map in ASSET_FILES:
            json_path = os.path.join(assets_dir, json_name)
            if not os.path.exists(json_path):
                print(f"Warning: asset file not found for scenario {label}: {json_path}")
                continue
            with open(json_path) as f:
                data = json.load(f)
            json_to_csv_transforms(data, output_path=os.path.join(out_dir, csv_name), field_map=field_map)

    print("DONE JSON TURNED TO CSV FOR ALL SCENARIOS")
