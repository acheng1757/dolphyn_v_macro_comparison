import json
import csv
import io
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
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
        ("elec_consumption",           "id",                  "elec_consumption"),
        ("h2_consumption",           "id",                  "h2_consumption"),
        ("natgas_consumption",           "id",                  "natgas_consumption"),
        ("ethylene_production", "id",                  "ethylene_production"),
        ("process_capture_rate",             "id",                  "process_capture_rate"),
        ("process_emission_rate",            "id",                  "process_emission_rate"),
        ("fuel_capture_rate",             "id",                  "fuel_capture_rate"),
        ("fuel_emission_rate",            "id",                  "fuel_emission_rate"),
        ("investment_cost",        "id", "investment_cost"),
        ("fixed_om_cost",          "id", "fixed_om_cost"),
        ("variable_om_cost",             "id", "variable_om_cost"),
    ]

# (json filename in <scenario>/assets/, output csv filename, field_map override)
ASSET_FILES = [
    ("ethanol_dehydration.json", "ethanol_dehydration.csv", DEFAULT_FIELD_MAP),
]


if __name__ == "__main__":
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
